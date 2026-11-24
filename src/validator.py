from decimal import Decimal
from datetime import date


def validate_invoice(invoice):
    errors = []

    required_fields = [
        "invoice_number",
        "vendor",
        "date",
        "currency",
        "subtotal",
        "tax",
        "total"
    ]

    # Check required fields.
    for field in required_fields:
        if invoice.get(field) is None:
            errors.append(f"Missing or invalid {field}")

    # Validate invoice date.
    if invoice.get("date") is not None:
        if not isinstance(invoice["date"], date):
            errors.append("Invalid invoice date")

    # Validate monetary values.
    for field in ["subtotal", "tax", "total"]:
        if invoice.get(field) is not None:
            if not isinstance(invoice[field], Decimal):
                errors.append(f"Invalid {field} amount")

    # Check arithmetic independently of other validation errors.
    subtotal = invoice.get("subtotal")
    tax = invoice.get("tax")
    total = invoice.get("total")

    if (
        isinstance(subtotal, Decimal)
        and isinstance(tax, Decimal)
        and isinstance(total, Decimal)
    ):
        if subtotal + tax != total:
            errors.append("Subtotal + tax does not equal total")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
