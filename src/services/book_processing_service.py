"""
Book Processing Service.

Main service that orchestrates the EPUB to flashcards workflow.
Handles file discovery, parsing, and error management.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..config.settings import AppConfig
from ..parsers.epub_parser import EpubParser, EpubParsingError
from ..models.book import Book
from ..models.flashcard import FlashCard
from .openai_flashcard_generator import OpenAIFlashcardGenerator
from .flashcard_persistence_service import FlashcardPersistenceService


class BookProcessingService:
    """
    Service for processing EPUB files into structured book data.
    
    This service coordinates the entire workflow:
    1. Discovering EPUB files in the configured directory
    2. Parsing each EPUB file using the EpubParser
    3. Handling errors gracefully
    4. Providing processing summaries
    """
    
    def __init__(self, config: AppConfig, epub_parser: EpubParser):
        """
        Initialize the service with dependencies.
        
        Args:
            config: Application configuration
            epub_parser: EPUB parsing component
        """
        self.config = config
        self.epub_parser = epub_parser
        self.logger = logging.getLogger(__name__)
        
        # Initialize flashcard-related services if enabled
        self.flashcard_generator = None
        self.persistence_service = None
        
        if config.generate_flashcards and config.openai_api_key:
            try:
                api_key = config.openai_api_key.get_secret_value()
                self.flashcard_generator = OpenAIFlashcardGenerator(api_key)
                self.persistence_service = FlashcardPersistenceService(config.output_folder)
                self.logger.info("Flashcard generation enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize flashcard generator: {e}")
                self.logger.warning("Continuing without flashcard generation")
        elif config.generate_flashcards and not config.openai_api_key:
            self.logger.warning("Flashcard generation enabled but no OpenAI API key provided")
        
        # Configure logging based on debug mode
        if config.debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    
    def discover_epub_files(self) -> List[Path]:
        """
        Discover all EPUB files in the configured ebooks folder.
        
        Returns:
            List[Path]: List of EPUB file paths
        """
        epub_files = []
        
        if not self.config.ebooks_folder.exists():
            self.logger.warning(f"Ebooks folder not found: {self.config.ebooks_folder}")
            return epub_files
        
        # Find all .epub files recursively
        for epub_file in self.config.ebooks_folder.rglob("*.epub"):
            epub_files.append(epub_file)
            self.logger.debug(f"Found EPUB file: {epub_file}")
        
        self.logger.info(f"Discovered {len(epub_files)} EPUB files")
        return epub_files
    
    def process_book(self, epub_path: Path) -> Book:
        """
        Process a single EPUB file into a Book object.
        
        Args:
            epub_path: Path to the EPUB file
            
        Returns:
            Book: Parsed book object
            
        Raises:
            EpubParsingError: If the book cannot be processed
        """
        self.logger.info(f"Processing book: {epub_path.name}")
        
        try:
            book = self.epub_parser.parse_epub(epub_path)
            self.logger.info(f"Successfully processed '{book.title}' with {book.total_chapters} chapters")
            return book
            
        except EpubParsingError as e:
            self.logger.error(f"Failed to process {epub_path.name}: {e}")
            raise
    
    def generate_flashcards_for_book(self, book: Book) -> Optional[List[FlashCard]]:
        """
        Generate flashcards for all chapters in a book.
        
        Args:
            book: The book to generate flashcards for
            
        Returns:
            List of generated flashcards, or None if generation is disabled/failed
        """
        if not self.flashcard_generator:
            self.logger.debug("Flashcard generation not available, skipping")
            return None
        
        self.logger.info(f"🗂️ Generating flashcards for '{book.title}' ({book.total_chapters} chapters)")
        all_flashcards = []
        
        for i, chapter in enumerate(book.chapters, 1):
            try:
                self.logger.info(f"📝 Processing chapter {i}/{book.total_chapters}: '{chapter.title}'")
                
                # Generate flashcards for this chapter
                chapter_flashcards = self.flashcard_generator.generate_flashcards(
                    chapter, 
                    num_flashcards=self.config.flashcards_per_chapter
                )
                
                all_flashcards.extend(chapter_flashcards)
                
                if chapter_flashcards:
                    self.logger.info(f"✅ Generated {len(chapter_flashcards)} flashcards for chapter '{chapter.title}'")
                    # Log each flashcard for visibility
                    for j, card in enumerate(chapter_flashcards, 1):
                        self.logger.info(f"   🔸 Flashcard {j}: {card.front[:80]}{'...' if len(card.front) > 80 else ''}")
                        self.logger.debug(f"      Front: {card.front}")
                        self.logger.debug(f"      Back: {card.back}")
                        self.logger.debug(f"      Type: {card.card_type}, Tags: {card.tags}")
                else:
                    self.logger.warning(f"⚠️ No flashcards generated for chapter '{chapter.title}'")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to generate flashcards for chapter '{chapter.title}': {e}")
                continue
        
        self.logger.info(f"🎯 Generated {len(all_flashcards)} total flashcards for '{book.title}'")
        return all_flashcards
    
    def _save_flashcards(self, book: Book, flashcards: List[FlashCard]) -> None:
        """
        Save flashcards in the configured format.
        
        Args:
            book: The book object
            flashcards: List of flashcards to save
        """
        if not self.persistence_service:
            return
        
        format_type = self.config.flashcard_output_format.lower()
        
        try:
            if format_type == "json":
                self.persistence_service.save_flashcards_json(book, flashcards)
            elif format_type == "csv":
                self.persistence_service.save_flashcards_csv(book, flashcards)
            elif format_type == "anki":
                self.persistence_service.save_flashcards_anki(book, flashcards)
            else:
                # Default to JSON if unknown format
                self.logger.warning(f"Unknown flashcard format '{format_type}', defaulting to JSON")
                self.persistence_service.save_flashcards_json(book, flashcards)
        except Exception as e:
            self.logger.error(f"Failed to save flashcards for '{book.title}': {e}")
    
    def process_all_books(self) -> tuple[List[Book], Dict[str, List[FlashCard]]]:
        """
        Process all discovered EPUB files and generate flashcards.
        
        Returns:
            Tuple of (List of books, Dictionary mapping book titles to flashcards)
        """
        epub_files = self.discover_epub_files()
        books = []
        all_flashcards = {}
        
        for epub_file in epub_files:
            try:
                # Process the book
                book = self.process_book(epub_file)
                books.append(book)
                
                # Generate flashcards if enabled
                if self.config.generate_flashcards and self.flashcard_generator:
                    flashcards = self.generate_flashcards_for_book(book)
                    if flashcards:
                        all_flashcards[book.title] = flashcards
                        
                        # Save flashcards in the configured format
                        self._save_flashcards(book, flashcards)
                
            except Exception as e:  # Catch all exceptions, not just EpubParsingError
                self.logger.error(f"Skipping {epub_file.name} due to error: {e}")
                continue
        
        # Save overall summary if flashcards were generated
        if all_flashcards and self.persistence_service:
            self.persistence_service.save_processing_summary(books, all_flashcards)
        
        self.logger.info(f"Successfully processed {len(books)} out of {len(epub_files)} books")
        if all_flashcards:
            total_flashcards = sum(len(cards) for cards in all_flashcards.values())
            self.logger.info(f"Generated {total_flashcards} total flashcards across all books")
        
        return books, all_flashcards
    
    def get_processing_summary(self, books: List[Book]) -> Dict[str, Any]:
        """
        Generate a summary of processing results.
        
        Args:
            books: List of processed books
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        summary = {
            'total_books': len(books),
            'total_chapters': sum(book.total_chapters for book in books),
            'total_words': sum(book.total_word_count for book in books),
            'books': [
                {
                    'title': book.title,
                    'author': book.author,
                    'chapters': book.total_chapters,
                    'words': book.total_word_count
                }
                for book in books
            ]
        }
        
        self.logger.info(f"Processing summary: {summary['total_books']} books, "
                        f"{summary['total_chapters']} chapters, "
                        f"{summary['total_words']} words")
        
        return summary
