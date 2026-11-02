"""Extract page text from the stored IRS PDFs into corpus/text, one JSONL file per publication."""

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

PDF_DIR = Path("corpus/pdf")
OUT_DIR = Path("corpus/text")


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    expected = dict(reversed(line.split()) for line in Path("corpus/SHA256SUMS").read_text().splitlines())
    for path in sorted(PDF_DIR.glob("*.pdf")):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[path.name], path.name
        publication = path.name.removeprefix("p").split("--")[0]
        reader = PdfReader(path)
        with (OUT_DIR / f"{publication}.jsonl").open("w") as handle:
            for number, page in enumerate(reader.pages, start=1):
                row = {"publication": publication, "page": number, "text": page.extract_text() or ""}
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(publication, len(reader.pages))


if __name__ == "__main__":
    main()
