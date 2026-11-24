import csv
from pathlib import Path

from ocr import process_images
from extractor import extract_invoice_data
from validator import validate_invoice
from database import create_tables, save_invoice, save_for_review


def generate_report(results):
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "report.csv"

    columns = [
        "filename",
        "status",
        "invoice_number",
        "vendor",
        "date",
        "currency",
        "subtotal",
        "tax",
        "total",
        "reasons"
    ]

    with open(report_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nReport generated: {report_file}")


def main():
    print("Starting Invoice OCR Processing...\n")

    # Create database tables
    create_tables()

    # Process all invoice images using OCR
    ocr_results = process_images()

    report_results = []

    for result in ocr_results:

        filename = result["filename"]

        # Handle OCR failures
        if result["status"] == "failed":
            report_results.append({
                "filename": filename,
                "status": "failed",
                "reasons": result.get("error", "OCR processing failed")
            })
            continue

        try:
            # Extract structured invoice data
            invoice = extract_invoice_data(result["raw_text"])

            # Display extracted values
            print(f"\nExtracted data for {filename}:")
            print(invoice)

            # Validate extracted data
            validation = validate_invoice(invoice)

            if validation["valid"]:

                # Store valid invoice and source scan
                save_invoice(
                    invoice,
                    filename,
                    result["raw_text"]
                )

                status = "valid"
                reasons = ""

            else:
                # Store invoice and original OCR text for manual review
                save_for_review(
                    filename,
                    invoice,
                    validation["errors"],
                    result["raw_text"]
                )

                status = "needs_review"
                reasons = "; ".join(validation["errors"])

            # Prepare CSV report row
            report_results.append({
                "filename": filename,
                "status": status,
                "invoice_number": invoice.get("invoice_number"),
                "vendor": invoice.get("vendor"),
                "date": invoice.get("date"),
                "currency": invoice.get("currency"),
                "subtotal": invoice.get("subtotal"),
                "tax": invoice.get("tax"),
                "total": invoice.get("total"),
                "reasons": reasons
            })

            print(f"{filename}: {status}")

        except Exception as error:
            report_results.append({
                "filename": filename,
                "status": "failed",
                "reasons": str(error)
            })

            print(f"{filename}: Failed - {error}")

    # Generate final CSV report
    generate_report(report_results)

    print("\nInvoice processing completed.")


if __name__ == "__main__":
    main()