"""
Book Processing Service.

Main service that orchestrates the EPUB to flashcards workflow.
Handles file discovery, parsing, and error management.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

from ..config.settings import AppConfig
from ..parsers.epub_parser import EpubParser, EpubParsingError
from ..models.book import Book


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
    
    def process_all_books(self) -> List[Book]:
        """
        Process all discovered EPUB files.
        
        Returns:
            List[Book]: List of successfully processed books
        """
        epub_files = self.discover_epub_files()
        books = []
        
        for epub_file in epub_files:
            try:
                book = self.process_book(epub_file)
                books.append(book)
            except Exception as e:  # Catch all exceptions, not just EpubParsingError
                self.logger.error(f"Skipping {epub_file.name} due to error: {e}")
                continue
        
        self.logger.info(f"Successfully processed {len(books)} out of {len(epub_files)} books")
        return books
    
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
