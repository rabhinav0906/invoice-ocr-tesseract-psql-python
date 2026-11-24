# Invoice OCR and Validation System

## Project Overview

This project automates invoice processing using Python and Tesseract OCR.

It reads invoice images, extracts important invoice details, validates the extracted information, and stores valid invoices in a PostgreSQL database. Incomplete or ambiguous invoices are flagged for manual review.

## Technologies Used

- Python
- Tesseract OCR
- Pytesseract
- Pillow
- PostgreSQL
- Psycopg
- Pytest

## Project Structure

```text
invoice-ocr-project/
├── invoices/
│   └── Sample invoice images
├── src/
│   ├── main.py
│   ├── ocr.py
│   ├── extractor.py
│   ├── validator.py
│   └── database.py
├── output/
│   ├── ocr_text/
│   └── report.csv
├── tests/
│   └── test_invoice.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Install Tesseract OCR

On Ubuntu:

```bash
sudo apt update
sudo apt install tesseract-ocr
```

Verify installation:

```bash
tesseract --version
```

### 2. Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Make sure PostgreSQL is installed and running.

Create a database named `invoice_db` and a database user named `invoice_user`, and configure the connection details in `src/database.py`.

The application creates the required tables automatically when it runs.

## Running the Application

From the project root directory:

```bash
source venv/bin/activate
python src/main.py
```

The application:

1. Reads invoice images from the `invoices/` directory.
2. Performs OCR using Tesseract.
3. Saves raw OCR text in `output/ocr_text/`.
4. Extracts invoice number, vendor, date, currency, subtotal, tax and total.
5. Validates required fields and total calculations.
6. Stores valid invoices in PostgreSQL.
7. Sends incomplete or ambiguous invoices to `review_records`.
8. Generates `output/report.csv`.

## Running Tests

Run:

```bash
python -m pytest -v
```

The tests cover:

- Validation of a valid invoice.
- Duplicate invoice imports and repeated scans.
- Incomplete or ambiguous invoice data.

## Database Design

The application uses three tables:

- **invoices:** Stores validated, unique invoice records.
- **source_scans:** Stores source filenames and their raw OCR text, including duplicate invoice scans.
- **review_records:** Stores extracted data and reasons for invoices requiring manual review.

The combination of normalized vendor name and invoice number prevents duplicate invoice records.

Source scans are tracked separately so that duplicate invoices do not cause their original scans to be discarded.

## Assumptions

- Invoice images are provided in PNG format.
- Invoices contain identifiable labels such as Invoice, Vendor, Date, Currency, Subtotal, Tax and Total.
- Invoice amounts use a format that can be normalized into decimal values.
- The database is available before processing begins.

## Limitations

- The current extraction patterns are designed around the supplied invoice format and may need adjustment for significantly different invoice layouts.
- OCR accuracy depends on image quality, text clarity and layout.
- Handwritten or unclear invoice fields may require manual review.
- The current input processing targets PNG files.

## Future Improvements

- Add a human correction step for invoices marked `needs_review`, allowing corrected values to be validated and saved.
- Add retry handling for temporary OCR or database failures.
- Support additional invoice layouts and image formats.
- Improve extraction using more advanced document-processing techniques.