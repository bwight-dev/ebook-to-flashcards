#!/usr/bin/env python3
"""
Test script for PDF parsing functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import AppConfig
from src.parsers.pdf_parser import PdfParser


def test_pdf_parser():
    """Test the PDF parser setup."""
    print("🔧 Testing PDF Parser Setup...")

    # Initialize configuration
    config = AppConfig()
    print(f"✅ Configuration loaded")
    print(f"   PDF folder: {config.pdf_folder}")
    print(f"   Pages per chapter fallback: {config.pdf_pages_per_chapter}")

    # Initialize PDF parser
    try:
        pdf_parser = PdfParser(config)
        print(f"✅ PDF Parser initialized successfully")

        # Check if PyMuPDF is working
        import fitz

        print(f"✅ PyMuPDF (fitz) version: {fitz.version[0]}")

        # Check for PDF files
        pdf_files = list(config.pdf_folder.rglob("*.pdf"))
        print(f"📁 Found {len(pdf_files)} PDF files in {config.pdf_folder}")

        if pdf_files:
            print("   PDF files found:")
            for pdf_file in pdf_files[:5]:  # Show first 5
                print(f"   - {pdf_file.name}")
        else:
            print("   No PDF files found. Add some PDFs to test parsing.")

    except Exception as e:
        print(f"❌ Error testing PDF parser: {e}")
        return False

    print("\n🎉 PDF Parser setup test completed successfully!")
    return True


if __name__ == "__main__":
    test_pdf_parser()
