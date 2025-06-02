"""
FlashCard data model.

Represents a single flashcard generated from chapter content.
This model ensures type safety and data validation for flashcard data.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FlashCard(BaseModel):
    """
    Represents a single flashcard for learning.
    
    This model ensures type safety and data validation for flashcard data
    generated from book chapters.
    """
    
    front: str = Field(..., description="The question or prompt on the front of the card")
    back: str = Field(..., description="The answer or explanation on the back of the card")
    card_type: str = Field(..., description="Type of flashcard: basic, cloze, definition, qa")
    tags: List[str] = Field(default=[], description="Topic tags for categorization")
    source: str = Field(..., description="Source chapter or section this card was generated from")
    difficulty: Optional[int] = Field(default=None, description="Difficulty level from 1-5")
