#!/usr/bin/env python3
"""
Demo script showing PDF parsing and flashcard generation.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.settings import AppConfig
from src.parsers.pdf_parser import PdfParser
from src.parsers.epub_parser import EpubParser
from src.services.book_processing_service import BookProcessingService

def main():
    """Demonstrate PDF and EPUB processing."""
    print("📚 Ebook to Flashcards - PDF & EPUB Demo")
    print("=" * 50)
    
    # Initialize configuration
    config = AppConfig()
    print(f"🔧 Configuration loaded:")
    print(f"   EPUB folder: {config.ebooks_folder}")
    print(f"   PDF folder: {config.pdf_folder}")
    print(f"   Output folder: {config.output_folder}")
    print(f"   Supported formats: {config.supported_formats}")
    print(f"   PDF pages per chapter: {config.pdf_pages_per_chapter}")
    print()
    
    # Initialize parsers
    epub_parser = EpubParser(config)
    pdf_parser = PdfParser(config)
    
    # Initialize book processing service
    service = BookProcessingService(config, epub_parser, pdf_parser)
    
    # Discover all ebook files
    print("🔍 Discovering ebook files...")
    ebook_files = service.discover_ebook_files()
    
    if not ebook_files:
        print("📄 No ebook files found. Here's how to get started:")
        print()
        print("1. For EPUB files:")
        print(f"   - Add .epub files to: {config.ebooks_folder}")
        print()
        print("2. For PDF files:")
        print(f"   - Add .pdf files to: {config.pdf_folder}")
        print()
        print("3. Example:")
        print("   mkdir -p ebooks/pdf ebooks/epub")
        print("   cp your_book.pdf ebooks/pdf/")
        print("   cp your_book.epub ebooks/epub/")
        print("   python demo_ebook_processing.py")
        print()
        return
    
    print(f"📁 Found {len(ebook_files)} ebook files:")
    for file_path in ebook_files:
        print(f"   - {file_path.name} ({file_path.suffix.upper()})")
    print()
    
    # Process each book
    books = []
    for file_path in ebook_files:
        try:
            print(f"📖 Processing: {file_path.name}")
            book = service.process_book(file_path)
            books.append(book)
            
            print(f"   ✅ Title: {book.title}")
            print(f"   ✅ Author: {book.author}")
            print(f"   ✅ Chapters: {len(book.chapters)}")
            print(f"   ✅ Total words: {book.total_word_count:,}")
            print()
            
            # Show first few chapters
            if book.chapters:
                print("   📋 Chapters preview:")
                for i, chapter in enumerate(book.chapters[:3], 1):
                    print(f"      {i}. {chapter.title}")
                    word_count = len(chapter.content.split())
                    print(f"         ({word_count:,} words)")
                if len(book.chapters) > 3:
                    print(f"      ... and {len(book.chapters) - 3} more chapters")
                print()
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path.name}: {e}")
            print()
            continue
    
    if books:
        # Generate summary
        summary = service.get_processing_summary(books)
        print("📊 Processing Summary:")
        print(f"   📚 Total books processed: {summary['total_books']}")
        print(f"   📑 Total chapters: {summary['total_chapters']}")
        print(f"   📝 Total words: {summary['total_words']:,}")
        print()
        
        # Show flashcard generation info
        if config.generate_flashcards:
            if config.openai_api_key:
                print("🤖 Flashcard generation is ENABLED")
                print(f"   Target flashcards per chapter: {config.flashcards_per_chapter}")
                print(f"   Output format: {config.flashcard_output_format}")
                print("   To generate flashcards, run the full processing:")
                print("   python main.py")
            else:
                print("🤖 Flashcard generation is DISABLED")
                print("   Set OPENAI_API_KEY environment variable to enable")
        else:
            print("🤖 Flashcard generation is DISABLED in config")
        print()
        
        print("🎯 PDF Parsing Strategies Used:")
        print("   1. Table of Contents (TOC) extraction - most reliable")
        print("   2. Font-based heading detection - for structured PDFs")
        print("   3. Pattern-based chapter recognition - regex patterns")
        print("   4. Page-based splitting - fallback method")
        print()
        
        print("💡 Tips for better PDF parsing:")
        print("   - PDFs with bookmarks/TOC work best")
        print("   - Clear chapter headings improve detection")
        print("   - Adjust pdf_pages_per_chapter for fallback splitting")
        print("   - Text-based PDFs work better than scanned images")

if __name__ == "__main__":
    main()
