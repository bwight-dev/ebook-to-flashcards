#!/usr/bin/env python3
"""
Manual test script for PDF parsing.
Run this after adding a PDF to ebooks/pdf/ folder.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append("src")

from src.config.settings import AppConfig
from src.parsers.pdf_parser import PdfParser


def test_pdf_parsing():
    """Test PDF parsing with actual file."""

    # Initialize config and parser
    config = AppConfig()
    parser = PdfParser(config)

    # Find PDF files
    pdf_folder = Path("ebooks/pdf")
    pdf_files = list(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDF files found in ebooks/pdf/")
        print("Please add a PDF file to test with.")
        return

    print(f"📚 Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")

    # Test with first PDF
    test_pdf = pdf_files[0]
    print(f"\n🔍 Testing with: {test_pdf.name}")

    try:
        # Parse the PDF
        book = parser.parse_pdf(test_pdf)

        # Print results
        print(f"\n✅ Successfully parsed PDF!")
        print(f"📖 Title: {book.title}")
        print(f"👤 Author: {book.author}")
        print(f"📄 Total chapters: {len(book.chapters)}")
        print(f"📊 Total words: {book.total_word_count}")

        # Show chapter details
        print(f"\n📑 Chapters:")
        for i, chapter in enumerate(book.chapters, 1):
            word_count = len(chapter.content.split()) if chapter.content else 0
            preview = (
                chapter.content[:100] + "..."
                if chapter.content and len(chapter.content) > 100
                else chapter.content
            )
            print(f"  {i}. {chapter.title}")
            print(f"     Words: {word_count}")
            print(f"     Preview: {preview}")
            print()

    except Exception as e:
        print(f"❌ Error parsing PDF: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_pdf_parsing()
