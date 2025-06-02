"""
Book data model.

Represents an entire EPUB file containing multiple chapters.
This is the main container for our ebook data.
"""

from typing import List
from pydantic import BaseModel, Field, computed_field
from .chapter import Chapter


class Book(BaseModel):
    """
    Represents an entire EPUB book with its metadata and chapters.
    
    This model aggregates chapter data and provides computed properties
    for book-level statistics like total word count.
    """
    
    title: str = Field(..., description="The title of the book")
    author: str = Field(..., description="The author of the book")
    file_path: str = Field(..., description="Path to the original EPUB file")
    chapters: List[Chapter] = Field(default=[], description="List of chapters in the book")
    
    @computed_field
    @property
    def total_chapters(self) -> int:
        """
        Get the total number of chapters in the book.
        
        Returns:
            int: Number of chapters
        """
        return len(self.chapters)
    
    @computed_field
    @property
    def total_word_count(self) -> int:
        """
        Calculate the total word count across all chapters.
        
        Returns:
            int: Sum of word counts from all chapters
        """
        return sum(chapter.word_count for chapter in self.chapters)
