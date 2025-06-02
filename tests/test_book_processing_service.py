"""
Test module for the book processing service.

Following TDD approach - testing the service layer that orchestrates
the entire EPUB to flashcards workflow.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch


class TestBookProcessingService:
    """
    TDD Cycle 5: Book Processing Service
    
    This service orchestrates the entire workflow:
    1. Discovery of EPUB files
    2. Parsing each EPUB
    3. Processing chapters for flashcard generation
    """
    
    def test_service_initialization(self):
        """
        RED: This test will fail because BookProcessingService doesn't exist yet.
        
        Testing service initialization with dependencies.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig()
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        assert service.config == config
        assert service.epub_parser == epub_parser
    
    def test_discover_epub_files(self):
        """
        Testing discovery of EPUB files in the configured directory.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig()
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        epub_files = service.discover_epub_files()
        
        assert len(epub_files) > 0
        assert all(file.suffix == '.epub' for file in epub_files)
        assert any('Andrew Aziz' in file.name for file in epub_files)
    
    def test_process_single_book(self):
        """
        Testing processing of a single EPUB file.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig()
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        epub_path = Path("./ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub")
        book = service.process_book(epub_path)
        
        assert book is not None
        assert book.title is not None
        assert len(book.chapters) > 0
    
    def test_process_all_books(self):
        """
        Testing processing of all discovered EPUB files.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig()
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        books = service.process_all_books()
        
        assert len(books) > 0
        assert all(book.total_chapters > 0 for book in books)
    
    def test_service_handles_parsing_errors_gracefully(self):
        """
        Testing that service handles parsing errors without crashing.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        
        config = AppConfig()
        
        # Mock parser that raises errors
        mock_parser = Mock()
        mock_parser.parse_epub.side_effect = Exception("Parsing failed")
        
        service = BookProcessingService(config, mock_parser)
        
        # Should not crash, should return empty list
        books = service.process_all_books()
        assert books == []
    
    def test_service_with_debug_logging(self):
        """
        Testing that debug mode enables appropriate logging.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig(debug_mode=True)
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        # Should initialize without errors in debug mode
        assert service.config.debug_mode is True
    
    def test_get_processing_summary(self):
        """
        Testing that service can provide processing summary statistics.
        """
        from src.services.book_processing_service import BookProcessingService
        from src.config.settings import AppConfig
        from src.parsers.epub_parser import EpubParser
        
        config = AppConfig()
        epub_parser = EpubParser(config)
        service = BookProcessingService(config, epub_parser)
        
        books = service.process_all_books()
        summary = service.get_processing_summary(books)
        
        assert 'total_books' in summary
        assert 'total_chapters' in summary
        assert 'total_words' in summary
        assert summary['total_books'] == len(books)
        assert summary['total_chapters'] > 0
        assert summary['total_words'] > 0
