import psycopg
import json

from datetime import date
from decimal import Decimal


DB_CONFIG = {
    "dbname": "invoice_db",
    "user": "invoice_user",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}


def get_connection():
    return psycopg.connect(**DB_CONFIG)


def create_tables():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Stores each unique invoice
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id SERIAL PRIMARY KEY,
                    invoice_number VARCHAR(100) NOT NULL,
                    vendor VARCHAR(255) NOT NULL,
                    invoice_date DATE NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    subtotal NUMERIC(12,2) NOT NULL,
                    tax NUMERIC(12,2) NOT NULL,
                    total NUMERIC(12,2) NOT NULL
                );
            """)

            # Prevents duplicate invoices even when vendor
            # names have different capitalization or spaces.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                invoices_vendor_invoice_normalized_idx
                ON invoices (
                    LOWER(BTRIM(vendor)),
                    invoice_number
                );
            """)

            # Stores every source scan, including duplicate invoices.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS source_scans (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) UNIQUE NOT NULL,
                    raw_text TEXT,
                    invoice_id INTEGER REFERENCES invoices(id)
                );
            """)

            # Stores invoices that require manual review.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS review_records (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    extracted_data JSONB,
                    review_reasons TEXT[]
                );
            """)

            # One review record per source filename.
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                review_records_filename_unique_idx
                ON review_records (filename);
            """)


def save_invoice(invoice, filename, raw_text):
    with get_connection() as conn:
        with conn.cursor() as cur:

            # Insert the invoice only if it does not already exist.
            cur.execute("""
                INSERT INTO invoices (
                    invoice_number,
                    vendor,
                    invoice_date,
                    currency,
                    subtotal,
                    tax,
                    total
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (
                    (LOWER(BTRIM(vendor))),
                    invoice_number
                )
                DO NOTHING
                RETURNING id;
            """, (
                invoice["invoice_number"],
                invoice["vendor"].strip(),
                invoice["date"],
                invoice["currency"],
                invoice["subtotal"],
                invoice["tax"],
                invoice["total"]
            ))

            result = cur.fetchone()

            if result:
                invoice_id = result[0]
            else:
                # Find the existing invoice when it is a duplicate.
                cur.execute("""
                    SELECT id
                    FROM invoices
                    WHERE LOWER(BTRIM(vendor)) = LOWER(BTRIM(%s))
                    AND invoice_number = %s;
                """, (
                    invoice["vendor"],
                    invoice["invoice_number"]
                ))

                invoice_id = cur.fetchone()[0]

            # Save this source scan even if its invoice is a duplicate.
            cur.execute("""
                INSERT INTO source_scans (
                    filename,
                    raw_text,
                    invoice_id
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (filename)
                DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    invoice_id = EXCLUDED.invoice_id;
            """, (filename, raw_text, invoice_id))

            # Remove an old review entry if this scan is now valid.
            cur.execute("""
                DELETE FROM review_records
                WHERE filename = %s;
            """, (filename,))

            return invoice_id


def save_for_review(filename, invoice, reasons, raw_text):

    extracted_data = {
        key: str(value) if isinstance(value, (date, Decimal)) else value
        for key, value in invoice.items()
    }

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Preserve the original OCR text.
            # Clear invoice_id because this scan needs review.
            cur.execute("""
                INSERT INTO source_scans (
                    filename,
                    raw_text,
                    invoice_id
                )
                VALUES (%s, %s, NULL)
                ON CONFLICT (filename)
                DO UPDATE SET
                    raw_text = EXCLUDED.raw_text,
                    invoice_id = NULL;
            """, (filename, raw_text))

            # Insert or update the review record.
            cur.execute("""
                INSERT INTO review_records (
                    filename,
                    extracted_data,
                    review_reasons
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (filename)
                DO UPDATE SET
                    extracted_data = EXCLUDED.extracted_data,
                    review_reasons = EXCLUDED.review_reasons;
            """, (
                filename,
                json.dumps(extracted_data),
                reasons
            ))