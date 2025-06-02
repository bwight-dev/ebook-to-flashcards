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
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    print("🚀 EPUB to Flashcards Application")
    print("=" * 40)
    
    try:
        # Initialize configuration
        config = AppConfig()
        
        # Set debug logging if enabled
        if hasattr(config, 'debug_mode') and config.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        
        print(f"📚 Looking for EPUB files in: {config.ebooks_folder}")
        print(f"💾 Output folder: {config.output_folder}")
        
        # Display flashcard configuration
        if config.generate_flashcards:
            print(f"🗂️ Flashcard generation: ENABLED")
            print(f"  📄 Format: {config.flashcard_output_format}")
            print(f"  🎯 Cards per chapter: {config.flashcards_per_chapter}")
            if config.openai_api_key:
                print(f"  🔑 OpenAI API key: Configured")
            else:
                print(f"  ⚠️ OpenAI API key: NOT SET")
        else:
            print(f"🗂️ Flashcard generation: DISABLED")
        
        # Initialize components following dependency injection
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        # Process all books and generate flashcards
        print("\n🔍 Discovering and processing EPUB files...")
        books, all_flashcards = service.process_all_books()
        
        # Display summary
        if books:
            summary = service.get_processing_summary(books)
            total_flashcards = sum(len(cards) for cards in all_flashcards.values())
            
            print("\n📊 Processing Summary:")
            print(f"  📖 Total Books: {summary['total_books']}")
            print(f"  📑 Total Chapters: {summary['total_chapters']}")
            print(f"  📝 Total Words: {summary['total_words']:,}")
            if all_flashcards:
                print(f"  🗂️ Total Flashcards: {total_flashcards}")
            
            print("\n📚 Book Details:")
            for book_info in summary['books']:
                book_title = book_info['title']
                flashcard_count = len(all_flashcards.get(book_title, []))
                print(f"  • '{book_title}' by {book_info['author']}")
                print(f"    Chapters: {book_info['chapters']}, Words: {book_info['words']:,}")
                if flashcard_count > 0:
                    print(f"    Flashcards: {flashcard_count}")
            
            # Display flashcard generation summary
            if all_flashcards:
                print("\n🗂️ Flashcard Generation Summary:")
                print(f"  📄 Format: {config.flashcard_output_format.upper()}")
                print(f"  💾 Output folder: {config.output_folder}")
                print(f"  ⚙️ Cards per chapter: {config.flashcards_per_chapter}")
                
                # Show detailed flashcard breakdown
                print("\n📊 Flashcard Details by Book:")
                for book_title, flashcards in all_flashcards.items():
                    if flashcards:
                        print(f"  📖 '{book_title}': {len(flashcards)} flashcards")
                        for i, card in enumerate(flashcards[:3], 1):  # Show first 3 cards
                            print(f"    {i}. {card.front[:60]}{'...' if len(card.front) > 60 else ''}")
                        if len(flashcards) > 3:
                            print(f"    ... and {len(flashcards) - 3} more cards")
                
                print("  ✅ Flashcards saved successfully!")
            elif config.generate_flashcards:
                print("\n⚠️ Flashcard generation was enabled but no flashcards were generated.")
                if not config.openai_api_key:
                    print("    Missing OpenAI API key. Please set OPENAI_API_KEY environment variable.")
                else:
                    print("    Check the logs for more details about why flashcards weren't generated.")
        else:
            print("❌ No EPUB files found or processed successfully.")
            
    except Exception as e:
        print(f"❌ Application error: {e}")
        if config.debug_mode:
            raise


if __name__ == "__main__":
    main()
