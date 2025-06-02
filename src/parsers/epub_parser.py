"""
EPUB Parser module.

Core component for reading and parsing EPUB files into our data models.
Handles file validation, metadata extraction, and chapter processing.
"""

import logging
from pathlib import Path
from typing import List, Optional
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from ..config.settings import AppConfig
from ..models.book import Book
from ..models.chapter import Chapter


class EpubParsingError(Exception):
    """Custom exception for EPUB parsing errors."""
    pass


class EpubParser:
    """
    Parser for EPUB files that converts them into our data models.
    
    This class handles the core business logic of reading EPUB files,
    extracting metadata, and converting chapters into our standardized format.
    """
    
    def __init__(self, config: AppConfig):
        """
        Initialize the parser with configuration.
        
        Args:
            config: Application configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def parse_epub(self, epub_path: Path) -> Book:
        """
        Parse an EPUB file and return a Book object with chapters.
        
        Args:
            epub_path: Path to the EPUB file
            
        Returns:
            Book: Parsed book with metadata and chapters
            
        Raises:
            EpubParsingError: If the file cannot be read or parsed
        """
        if not epub_path.exists():
            raise EpubParsingError(f"File not found: {epub_path}")
        
        try:
            # Read the EPUB file
            book_data = epub.read_epub(str(epub_path))
            
            # Extract metadata
            title = self._extract_title(book_data)
            author = self._extract_author(book_data)
            
            # Extract chapters
            chapters = self._extract_chapters(book_data)
            
            # Apply chapter limit if configured
            if self.config.max_chapters_per_book:
                chapters = chapters[:self.config.max_chapters_per_book]
            
            return Book(
                title=title,
                author=author,
                file_path=str(epub_path),
                chapters=chapters
            )
            
        except Exception as e:
            if isinstance(e, EpubParsingError):
                raise
            raise EpubParsingError(f"Failed to parse EPUB {epub_path}: {str(e)}")
    
    def _extract_title(self, book_data) -> str:
        """Extract book title from EPUB metadata."""
        title = book_data.get_metadata('DC', 'title')
        if title:
            return title[0][0]  # Get first title
        return "Unknown Title"
    
    def _extract_author(self, book_data) -> str:
        """Extract author from EPUB metadata."""
        authors = book_data.get_metadata('DC', 'creator')
        if authors:
            return authors[0][0]  # Get first author
        return "Unknown Author"
    
    def _extract_chapters(self, book_data) -> List[Chapter]:
        """
        Extract chapters from EPUB content.
        
        Args:
            book_data: EPUB book object from ebooklib
            
        Returns:
            List[Chapter]: Ordered list of chapters
        """
        chapters = []
        chapter_number = 1
        
        # Process document items in spine order for correct sequencing
        for item_id, _ in book_data.spine:
            item = book_data.get_item_with_id(item_id)
            
            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapter = self._process_chapter_item(item, chapter_number)
                if chapter and chapter.content.strip():  # Only add non-empty chapters
                    chapters.append(chapter)
                    chapter_number += 1
        
        return chapters
    
    def _process_chapter_item(self, item, chapter_number: int) -> Optional[Chapter]:
        """
        Process a single chapter item from the EPUB.
        
        Args:
            item: EPUB item to process
            chapter_number: Sequential chapter number
            
        Returns:
            Chapter: Processed chapter or None if invalid
        """
        try:
            # Parse HTML content
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(strip=True, separator=' ')
            
            # Extract title (try multiple strategies)
            title = self._extract_chapter_title(soup, chapter_number)
            
            return Chapter(
                title=title,
                content=text_content,
                chapter_number=chapter_number,
                file_name=item.get_name()
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to process chapter {chapter_number}: {e}")
            return None
    
    def _extract_chapter_title(self, soup: BeautifulSoup, chapter_number: int) -> str:
        """
        Extract chapter title from HTML content.
        
        Args:
            soup: BeautifulSoup object of chapter content
            chapter_number: Fallback chapter number
            
        Returns:
            str: Chapter title
        """
        # Try different title extraction strategies
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        # Try heading tags
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading and heading.get_text().strip():
                return heading.get_text().strip()
        
        # Fallback to generic title
        return f"Chapter {chapter_number}"
