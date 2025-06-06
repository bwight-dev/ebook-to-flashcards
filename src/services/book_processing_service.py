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
from ..parsers.pdf_parser import PdfParser, PdfParsingError
from ..models.book import Book
from ..models.flashcard import FlashCard
from .openai_flashcard_generator import OpenAIFlashcardGenerator
from .flashcard_persistence_service import FlashcardPersistenceService


class BookProcessingService:
    """
    Service for processing EPUB and PDF files into structured book data.

    This service coordinates the entire workflow:
    1. Discovering ebook files in the configured directories
    2. Parsing each file using the appropriate parser (EPUB or PDF)
    3. Handling errors gracefully
    4. Providing processing summaries
    """

    def __init__(
        self,
        config: AppConfig,
        epub_parser: EpubParser,
        pdf_parser: Optional[PdfParser] = None,
    ):
        """
        Initialize the service with dependencies.

        Args:
            config: Application configuration
            epub_parser: EPUB parsing component
            pdf_parser: PDF parsing component (optional, will create if not provided)
        """
        self.config = config
        self.epub_parser = epub_parser
        self.pdf_parser = pdf_parser or PdfParser(config)
        self.logger = logging.getLogger(__name__)

        # Initialize flashcard-related services if enabled
        self.flashcard_generator = None
        self.persistence_service = None

        if config.generate_flashcards and config.openai_api_key:
            try:
                api_key = config.openai_api_key.get_secret_value()
                self.flashcard_generator = OpenAIFlashcardGenerator(api_key)
                self.persistence_service = FlashcardPersistenceService(
                    config.output_folder
                )
                self.logger.info("Flashcard generation enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize flashcard generator: {e}")
                self.logger.warning("Continuing without flashcard generation")
        elif config.generate_flashcards and not config.openai_api_key:
            self.logger.warning(
                "Flashcard generation enabled but no OpenAI API key provided"
            )
        # Configure logging based on debug mode
        if config.debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def discover_ebook_files(self) -> List[Path]:
        """
        Discover all supported ebook files in the configured folders.

        Returns:
            List[Path]: List of ebook file paths (EPUB and PDF)
        """
        ebook_files = []

        # EPUB files
        if self.config.ebooks_folder.exists():
            for epub_file in self.config.ebooks_folder.rglob("*.epub"):
                ebook_files.append(epub_file)
                self.logger.debug(f"Found EPUB file: {epub_file}")
        else:
            self.logger.warning(f"EPUB folder not found: {self.config.ebooks_folder}")

        # PDF files
        if self.config.pdf_folder.exists():
            for pdf_file in self.config.pdf_folder.rglob("*.pdf"):
                ebook_files.append(pdf_file)
                self.logger.debug(f"Found PDF file: {pdf_file}")
        else:
            self.logger.warning(f"PDF folder not found: {self.config.pdf_folder}")

        self.logger.info(f"Discovered {len(ebook_files)} ebook files")
        return ebook_files

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

    def process_book(self, file_path: Path) -> Book:
        """
        Process a single ebook file into a Book object (EPUB or PDF).

        Args:
            file_path: Path to the ebook file

        Returns:
            Book: Parsed book object
              Raises:
            EpubParsingError or PdfParsingError: If the book cannot be processed
        """
        self.logger.info(f"Processing book: {file_path.name}")

        try:
            if file_path.suffix.lower() == ".epub":
                book = self.epub_parser.parse_epub(file_path)
            elif file_path.suffix.lower() == ".pdf":
                book = self.pdf_parser.parse_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

            self.logger.info(
                f"Successfully processed '{book.title}' with {book.total_chapters} chapters"
            )
            return book

        except (EpubParsingError, PdfParsingError) as e:
            self.logger.error(f"Failed to process {file_path.name}: {e}")
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

        self.logger.info(
            f"🗂️ Generating flashcards for '{book.title}' ({book.total_chapters} chapters)"
        )
        all_flashcards = []

        for i, chapter in enumerate(book.chapters, 1):
            try:
                self.logger.info(
                    f"📝 Processing chapter {i}/{book.total_chapters}: '{chapter.title}'"
                )

                # Generate flashcards for this chapter
                chapter_flashcards = self.flashcard_generator.generate_flashcards(
                    chapter, num_flashcards=self.config.flashcards_per_chapter
                )

                all_flashcards.extend(chapter_flashcards)

                if chapter_flashcards:
                    self.logger.info(
                        f"✅ Generated {len(chapter_flashcards)} flashcards for chapter '{chapter.title}'"
                    )
                    # Log each flashcard for visibility
                    for j, card in enumerate(chapter_flashcards, 1):
                        self.logger.info(
                            f"   🔸 Flashcard {j}: {card.front[:80]}{'...' if len(card.front) > 80 else ''}"
                        )
                        self.logger.debug(f"      Front: {card.front}")
                        self.logger.debug(f"      Back: {card.back}")
                        self.logger.debug(
                            f"      Type: {card.card_type}, Tags: {card.tags}"
                        )
                else:
                    self.logger.warning(
                        f"⚠️ No flashcards generated for chapter '{chapter.title}'"
                    )

            except Exception as e:
                self.logger.error(
                    f"❌ Failed to generate flashcards for chapter '{chapter.title}': {e}"
                )
                continue

        self.logger.info(
            f"🎯 Generated {len(all_flashcards)} total flashcards for '{book.title}'"
        )
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
                self.logger.warning(
                    f"Unknown flashcard format '{format_type}', defaulting to JSON"
                )
                self.persistence_service.save_flashcards_json(book, flashcards)
        except Exception as e:
            self.logger.error(f"Failed to save flashcards for '{book.title}': {e}")
    
    def process_all_books(self) -> tuple[List[Book], Dict[str, List[FlashCard]]]:
        """
        Process all discovered ebook files and generate flashcards.
        
        Returns:
            Tuple of (List of books, Dictionary mapping book titles to flashcards)
        """
        ebook_files = self.discover_ebook_files()
        books = []
        all_flashcards = {}
        
        for ebook_file in ebook_files:
            try:
                # Process the book
                book = self.process_book(ebook_file)
                books.append(book)
                
                # Generate flashcards if enabled
                if self.config.generate_flashcards and self.flashcard_generator:
                    flashcards = self.generate_flashcards_for_book(book)
                    if flashcards:
                        all_flashcards[book.title] = flashcards
                        
                        # Save flashcards in the configured format
                        self._save_flashcards(book, flashcards)
                
            except Exception as e:  # Catch all exceptions, not just EpubParsingError
                self.logger.error(f"Skipping {ebook_file.name} due to error: {e}")
                continue
        
        # Save overall summary if flashcards were generated
        if all_flashcards and self.persistence_service:
            self.persistence_service.save_processing_summary(books, all_flashcards)
        
        self.logger.info(f"Successfully processed {len(books)} out of {len(ebook_files)} books")
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
            "total_books": len(books),
            "total_chapters": sum(book.total_chapters for book in books),
            "total_words": sum(book.total_word_count for book in books),
            "books": [
                {
                    "title": book.title,
                    "author": book.author,
                    "chapters": book.total_chapters,
                    "words": book.total_word_count,
                }
                for book in books
            ],
        }

        self.logger.info(
            f"Processing summary: {summary['total_books']} books, "
            f"{summary['total_chapters']} chapters, "
            f"{summary['total_words']} words"
        )

        return summary
