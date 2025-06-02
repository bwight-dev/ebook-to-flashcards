"""
Chapter data model.

This is our core data structure representing a single chapter from an EPUB file.
Following the principle of making tests pass with minimal code.
"""

from pydantic import BaseModel, Field, computed_field


class Chapter(BaseModel):
    """
    Represents a single chapter from an EPUB file.
    
    This model ensures type safety and data validation for chapter data.
    The word_count is automatically calculated from the content.
    """
    
    title: str = Field(..., description="The title of the chapter")
    content: str = Field(..., description="The text content of the chapter")
    chapter_number: int = Field(..., description="The sequential number of the chapter")
    file_name: str = Field(..., description="The original file name from the EPUB")
    
    @computed_field
    @property
    def word_count(self) -> int:
        """
        Calculate the number of words in the chapter content.
        
        Returns:
            int: Number of words in the content
        """
        if not self.content.strip():
            return 0
        return len(self.content.split())
