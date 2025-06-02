"""
Test module for data models.

Following TDD approach - start with the simplest data structure that our application needs:
a Chapter model that represents a single chapter from an EPUB file.
"""

import pytest
from pydantic import ValidationError


class TestChapterModel:
    """
    TDD Cycle 1: Chapter Data Model
    
    Starting with the most fundamental unit - a Chapter.
    This test defines the contract for what constitutes a chapter in our system.
    """
    
    def test_chapter_creation_with_valid_data(self):
        """
        RED: This test will fail because Chapter model doesn't exist yet.
        
        Testing the happy path - creating a chapter with all required fields.
        This establishes our data contract.
        """
        from src.models.chapter import Chapter
        
        chapter_data = {
            "title": "Introduction to Day Trading",
            "content": "Day trading is the practice of buying and selling...",
            "chapter_number": 1,
            "file_name": "chapter01.xhtml"
        }
        
        chapter = Chapter(**chapter_data)
        
        assert chapter.title == "Introduction to Day Trading"
        assert chapter.content == "Day trading is the practice of buying and selling..."
        assert chapter.chapter_number == 1
        assert chapter.file_name == "chapter01.xhtml"
        assert chapter.word_count > 0  # Should auto-calculate
    
    def test_chapter_word_count_calculation(self):
        """
        Testing that word count is automatically calculated from content.
        """
        from src.models.chapter import Chapter
        
        chapter = Chapter(
            title="Test Chapter",
            content="This is a test chapter with exactly nine words.",
            chapter_number=1,
            file_name="test.xhtml"
        )
        
        assert chapter.word_count == 9
    
    def test_chapter_validation_missing_required_fields(self):
        """
        Testing that Pydantic validation works for required fields.
        """
        from src.models.chapter import Chapter
        
        with pytest.raises(ValidationError) as exc_info:
            Chapter(content="Some content")  # Missing required fields
        
        errors = exc_info.value.errors()
        required_fields = {error['loc'][0] for error in errors}
        expected_required = {'title', 'chapter_number', 'file_name'}
        
        assert expected_required.issubset(required_fields)
    
    def test_chapter_with_empty_content(self):
        """
        Testing edge case - chapter with empty content should have word_count of 0.
        """
        from src.models.chapter import Chapter
        
        chapter = Chapter(
            title="Empty Chapter",
            content="",
            chapter_number=1,
            file_name="empty.xhtml"
        )
        
        assert chapter.word_count == 0


class TestBookModel:
    """
    TDD Cycle 2: Book Data Model
    
    A Book represents the entire EPUB file and contains multiple chapters.
    This establishes the container for our chapter data.
    """
    
    def test_book_creation_with_valid_data(self):
        """
        RED: This test will fail because Book model doesn't exist yet.
        
        Testing book creation with metadata and chapters.
        """
        from src.models.book import Book
        from src.models.chapter import Chapter
        
        chapters = [
            Chapter(
                title="Chapter 1",
                content="Content of chapter 1",
                chapter_number=1,
                file_name="ch01.xhtml"
            ),
            Chapter(
                title="Chapter 2", 
                content="Content of chapter 2",
                chapter_number=2,
                file_name="ch02.xhtml"
            )
        ]
        
        book = Book(
            title="How to Day Trade for a Living",
            author="Andrew Aziz",
            file_path="/workspaces/ebook-to-flash-cards/ebooks/epub/How to Day Trade for a Living_ - Andrew Aziz.epub",
            chapters=chapters
        )
        
        assert book.title == "How to Day Trade for a Living"
        assert book.author == "Andrew Aziz"
        assert len(book.chapters) == 2
        assert book.total_chapters == 2
        assert book.total_word_count > 0
    
    def test_book_with_no_chapters(self):
        """
        Testing edge case - book with no chapters should have appropriate defaults.
        """
        from src.models.book import Book
        
        book = Book(
            title="Empty Book",
            author="Unknown Author",
            file_path="/path/to/empty.epub",
            chapters=[]
        )
        
        assert book.total_chapters == 0
        assert book.total_word_count == 0
    
    def test_book_total_word_count_calculation(self):
        """
        Testing that total word count is sum of all chapter word counts.
        """
        from src.models.book import Book
        from src.models.chapter import Chapter
        
        chapters = [
            Chapter(
                title="Chapter 1",
                content="This has four words",  # 4 words
                chapter_number=1,
                file_name="ch01.xhtml"
            ),
            Chapter(
                title="Chapter 2",
                content="This chapter has five words total",  # 6 words
                chapter_number=2,
                file_name="ch02.xhtml"
            )
        ]
        
        book = Book(
            title="Test Book",
            author="Test Author", 
            file_path="/test/path.epub",
            chapters=chapters
        )
        
        assert book.total_word_count == 10  # 4 + 6 = 10
