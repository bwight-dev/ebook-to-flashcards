"""
Test module for EPUB parser.

Following TDD approach - testing the core EPUB parsing functionality
that reads EPUB files and extracts chapters.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestEpubParser:
    """
    TDD Cycle 4: EPUB Parser
    
    This is the core component that reads EPUB files and converts them
    into our Book and Chapter data models.
    """
    
    def test_parser_initialization(self):
        """
        RED: This test will fail because EpubParser doesn't exist yet.
        
        Testing that parser can be initialized with configuration.
        """
        from src.parsers.epub_parser import EpubParser
        from src.config.settings import AppConfig
        
        config = AppConfig()
        parser = EpubParser(config)
        
        assert parser.config == config
    
    def test_parse_existing_epub_file(self):
        """
        Testing parsing of our actual EPUB file.
        This is an integration test with real data.
        """
        from src.parsers.epub_parser import EpubParser
        from src.config.settings import AppConfig
        
        config = AppConfig()
        parser = EpubParser(config)
        
        epub_path = Path("./ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub")
        book = parser.parse_epub(epub_path)
        
        assert book.title is not None
        assert book.author is not None
        assert book.file_path == str(epub_path)
        assert len(book.chapters) > 0
        assert book.total_word_count > 0
    
    def test_parse_nonexistent_file_raises_error(self):
        """
        Testing error handling for missing files.
        """
        from src.parsers.epub_parser import EpubParser, EpubParsingError
        from src.config.settings import AppConfig
        
        config = AppConfig()
        parser = EpubParser(config)
        
        with pytest.raises(EpubParsingError) as exc_info:
            parser.parse_epub(Path("./nonexistent.epub"))
        
        assert "File not found" in str(exc_info.value)
    
    def test_parse_with_chapter_limit(self):
        """
        Testing that parser respects max_chapters_per_book configuration.
        """
        from src.parsers.epub_parser import EpubParser
        from src.config.settings import AppConfig
        
        config = AppConfig(max_chapters_per_book=2)
        parser = EpubParser(config)
        
        epub_path = Path("./ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub")
        book = parser.parse_epub(epub_path)
        
        assert len(book.chapters) <= 2
    
    @patch('ebooklib.epub.read_epub')
    @patch('pathlib.Path.exists')
    def test_parse_corrupted_epub_raises_error(self, mock_exists, mock_read_epub):
        """
        Testing error handling for corrupted EPUB files.
        Using mocking to simulate file corruption.
        """
        from src.parsers.epub_parser import EpubParser, EpubParsingError
        from src.config.settings import AppConfig
        
        # Mock file existence and ebooklib to raise an exception
        mock_exists.return_value = True
        mock_read_epub.side_effect = Exception("Corrupted EPUB")
        
        config = AppConfig()
        parser = EpubParser(config)
        
        with pytest.raises(EpubParsingError) as exc_info:
            parser.parse_epub(Path("./corrupted.epub"))
        
        assert "Failed to parse EPUB" in str(exc_info.value)
    
    def test_extract_book_metadata(self):
        """
        Testing metadata extraction from EPUB files.
        """
        from src.parsers.epub_parser import EpubParser
        from src.config.settings import AppConfig
        
        config = AppConfig()
        parser = EpubParser(config)
        
        epub_path = Path("./ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub")
        book = parser.parse_epub(epub_path)
        
        # Should extract title and author
        assert "Day Trade" in book.title or "Andrew Aziz" in book.author
        assert book.file_path == str(epub_path)
    
    def test_chapter_ordering_is_correct(self):
        """
        Testing that chapters are extracted in the correct order.
        """
        from src.parsers.epub_parser import EpubParser
        from src.config.settings import AppConfig
        
        config = AppConfig()
        parser = EpubParser(config)
        
        epub_path = Path("./ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub")
        book = parser.parse_epub(epub_path)
        
        # Chapters should be numbered sequentially
        for i, chapter in enumerate(book.chapters, 1):
            assert chapter.chapter_number == i
