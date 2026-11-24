from datetime import date
from decimal import Decimal

from src.extractor import extract_invoice_data
from src.validator import validate_invoice
from src.database import create_tables, get_connection, save_invoice


# Test 1: Valid invoice
def test_valid_invoice():
    invoice = {
        "invoice_number": "TEST-101",
        "vendor": "ABC Ltd",
        "date": date(2026, 11, 20),
        "currency": "INR",
        "subtotal": Decimal("1000.00"),
        "tax": Decimal("180.00"),
        "total": Decimal("1180.00")
    }

    result = validate_invoice(invoice)

    assert result["valid"] is True
    assert result["errors"] == []


# Test 2: Duplicate invoice and repeated imports
def test_duplicate_import():
    create_tables()

    invoice_a = {
        "invoice_number": "TEST-DUP-101",
        "vendor": "Test Vendor",
        "date": date(2026, 11, 20),
        "currency": "INR",
        "subtotal": Decimal("1000.00"),
        "tax": Decimal("180.00"),
        "total": Decimal("1180.00")
    }

    invoice_b = {
        **invoice_a,
        "vendor": "TEST VENDOR"
    }

    filenames = ["test-scan-a.png", "test-scan-b.png"]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM source_scans WHERE filename = ANY(%s)",
                    (filenames,)
                )
                cur.execute("""
                    DELETE FROM invoices
                    WHERE invoice_number = %s
                    AND LOWER(BTRIM(vendor)) = LOWER(BTRIM(%s))
                """, ("TEST-DUP-101", "Test Vendor"))

        save_invoice(invoice_a, filenames[0], "OCR text A")
        save_invoice(invoice_b, filenames[1], "OCR text B")
        save_invoice(invoice_a, filenames[0], "OCR text A")

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM invoices
                    WHERE invoice_number = %s
                    AND LOWER(BTRIM(vendor)) = LOWER(BTRIM(%s))
                """, ("TEST-DUP-101", "Test Vendor"))

                invoice_count = cur.fetchone()[0]

                cur.execute("""
                    SELECT COUNT(*) FROM source_scans
                    WHERE filename = ANY(%s)
                """, (filenames,))

                scan_count = cur.fetchone()[0]

        assert invoice_count == 1
        assert scan_count == 2

    finally:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM source_scans WHERE filename = ANY(%s)",
                    (filenames,)
                )
                cur.execute("""
                    DELETE FROM invoices
                    WHERE invoice_number = %s
                    AND LOWER(BTRIM(vendor)) = LOWER(BTRIM(%s))
                """, ("TEST-DUP-101", "Test Vendor"))


# Test 3: Incomplete or ambiguous invoice
def test_incomplete_invoice():
    raw_text = """
    Invoice: TEST-103
    Vendor: ABC Ltd
    Date: 2026-11-20
    Currency: INR
    Subtotal: 1000.00
    Tax: 180.00
    Total: 11?0.00
    """

    invoice = extract_invoice_data(raw_text)
    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert len(result["errors"]) > 0