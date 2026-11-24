import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


def extract_invoice_data(raw_text):
    patterns = {
        "invoice_number": r"^Invoice:\s*(.+)$",
        "vendor": r"^Vendor:\s*(.+)$",
        "date": r"^Date:\s*(.+)$",
        "currency": r"^Currency:\s*(.+)$",
        "subtotal": r"^Subtotal:\s*(.+)$",
        "tax": r"^Tax:\s*(.+)$",
        "total": r"^Total:\s*(.+)$"
    }

    invoice = {}

    for field, pattern in patterns.items():
        match = re.search(
            pattern,
            raw_text,
            re.IGNORECASE | re.MULTILINE
        )

        value = match.group(1).strip() if match else ""
        invoice[field] = value if value else None

    # Normalize date
    if invoice["date"]:
        for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                invoice["date"] = datetime.strptime(
                    invoice["date"], date_format
                ).date()
                break
            except ValueError:
                continue

    # Normalize monetary values
    for field in ["subtotal", "tax", "total"]:
        value = invoice[field]

        if value:
            try:
                invoice[field] = Decimal(
                    value.replace(",", "").replace("₹", "").strip()
                )
            except InvalidOperation:
                invoice[field] = None

    return invoice