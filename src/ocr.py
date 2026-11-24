import pytesseract
from pytesseract import Output
from PIL import Image
from pathlib import Path


def extract_text(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)


def get_ocr_confidence(image_path):
    image = Image.open(image_path)

    data = pytesseract.image_to_data(
        image,
        output_type=Output.DICT
    )

    low_confidence_words = []

    for word, confidence in zip(data["text"], data["conf"]):
        word = word.strip()

        try:
            confidence = float(confidence)
        except ValueError:
            continue

        if word and confidence >= 0 and confidence < 60:
            low_confidence_words.append({
                "word": word,
                "confidence": confidence
            })

    return low_confidence_words


def process_images():
    input_dir = Path("invoices")
    output_dir = Path("output/ocr_text")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for image_path in sorted(input_dir.glob("*.png")):
        try:
            raw_text = extract_text(image_path)

            low_confidence_words = get_ocr_confidence(image_path)

            output_file = output_dir / f"{image_path.stem}.txt"
            output_file.write_text(raw_text, encoding="utf-8")

            results.append({
                "filename": image_path.name,
                "raw_text": raw_text,
                "low_confidence_words": low_confidence_words,
                "status": "success"
            })

            print(f"Processed: {image_path.name}")

        except Exception as error:
            results.append({
                "filename": image_path.name,
                "raw_text": "",
                "low_confidence_words": [],
                "status": "failed",
                "error": str(error)
            })

            print(f"Failed: {image_path.name}: {error}")

    return results