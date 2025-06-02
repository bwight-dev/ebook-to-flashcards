"""
Main entry point for the EPUB to Flashcards application.

Demonstrates the complete TDD-built architecture working together.
"""

import logging
from pathlib import Path

from src.config.settings import AppConfig
from src.parsers.epub_parser import EpubParser
from src.services.book_processing_service import BookProcessingService


def main():
    """
    Main application entry point.
    
    Demonstrates the complete workflow:
    1. Load configuration
    2. Initialize components
    3. Process EPUB files
    4. Display results
    """
    print("🚀 EPUB to Flashcards Application")
    print("=" * 40)
    
    try:
        # Initialize configuration
        config = AppConfig()
        print(f"📚 Looking for EPUB files in: {config.ebooks_folder}")
        print(f"💾 Output folder: {config.output_folder}")
        
        # Initialize components following dependency injection
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        # Process all books
        print("\n🔍 Discovering and processing EPUB files...")
        books = service.process_all_books()
        
        # Display summary
        if books:
            summary = service.get_processing_summary(books)
            print("\n📊 Processing Summary:")
            print(f"  📖 Total Books: {summary['total_books']}")
            print(f"  📑 Total Chapters: {summary['total_chapters']}")
            print(f"  📝 Total Words: {summary['total_words']:,}")
            
            print("\n📚 Book Details:")
            for book_info in summary['books']:
                print(f"  • '{book_info['title']}' by {book_info['author']}")
                print(f"    Chapters: {book_info['chapters']}, Words: {book_info['words']:,}")
        else:
            print("❌ No EPUB files found or processed successfully.")
            
    except Exception as e:
        print(f"❌ Application error: {e}")
        if config.debug_mode:
            raise


if __name__ == "__main__":
    main()
