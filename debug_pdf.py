from app.parser.pdf_parser import parse_pdf

pages = parse_pdf("data/uploads/SAMPLE (2).pdf")

with open("data/uploads/pdf_lines.txt", "w", encoding="utf-8") as f:
    for page in pages:
        f.write(f"\n===== PAGE {page.page_number} =====\n")

        for i, line in enumerate(page.text.splitlines(), start=1):
            if line.strip():
                f.write(f"{i}: {line}\n")

print("Saved:", len(pages), "pages")
