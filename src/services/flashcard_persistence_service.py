"""
Flashcard Persistence Service.

Handles saving and exporting flashcards in various formats including JSON, CSV, and Anki.
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..models.flashcard import FlashCard
from ..models.book import Book


logger = logging.getLogger(__name__)


class FlashcardPersistenceService:
    """
    Service for persisting flashcards in various formats.
    
    Supports JSON, CSV, and Anki deck formats for flashcard storage and export.
    """
    
    def __init__(self, output_folder: Path):
        """
        Initialize the persistence service.
        
        Args:
            output_folder: Path to the output directory
        """
        self.output_folder = output_folder
        self.logger = logging.getLogger(__name__)
        
        # Ensure output folder exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
    
    def save_flashcards_json(self, book: Book, flashcards: List[FlashCard]) -> Path:
        """
        Save flashcards as JSON file.
        
        Args:
            book: The book object
            flashcards: List of flashcards to save
            
        Returns:
            Path to the saved JSON file
        """
        # Create filename with book title (sanitized)
        safe_title = self._sanitize_filename(book.title)
        filename = f"{safe_title}_flashcards.json"
        filepath = self.output_folder / filename
        
        # Prepare data structure
        data = {
            "metadata": {
                "book_title": book.title,
                "book_author": book.author,
                "generated_at": datetime.now().isoformat(),
                "total_flashcards": len(flashcards),
                "total_chapters": book.total_chapters
            },
            "flashcards": [
                {
                    "front": card.front,
                    "back": card.back,
                    "card_type": card.card_type,
                    "source": card.source,
                    "difficulty": card.difficulty,
                    "tags": card.tags
                }
                for card in flashcards
            ]
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(flashcards)} flashcards to JSON: {filepath}")
        return filepath
    
    def save_flashcards_csv(self, book: Book, flashcards: List[FlashCard]) -> Path:
        """
        Save flashcards as CSV file.
        
        Args:
            book: The book object
            flashcards: List of flashcards to save
            
        Returns:
            Path to the saved CSV file
        """
        # Create filename with book title (sanitized)
        safe_title = self._sanitize_filename(book.title)
        filename = f"{safe_title}_flashcards.csv"
        filepath = self.output_folder / filename
        
        # Define CSV headers
        headers = ['front', 'back', 'card_type', 'source', 'difficulty', 'tags']
        
        # Save to file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for card in flashcards:
                writer.writerow([
                    card.front,
                    card.back,
                    card.card_type,
                    card.source,
                    card.difficulty,
                    ','.join(card.tags) if card.tags else ''
                ])
        
        self.logger.info(f"Saved {len(flashcards)} flashcards to CSV: {filepath}")
        return filepath
    
    def save_flashcards_anki(self, book: Book, flashcards: List[FlashCard]) -> Path:
        """
        Save flashcards in Anki import format (tab-separated values).
        
        Args:
            book: The book object
            flashcards: List of flashcards to save
            
        Returns:
            Path to the saved Anki file
        """
        # Create filename with book title (sanitized)
        safe_title = self._sanitize_filename(book.title)
        filename = f"{safe_title}_flashcards_anki.txt"
        filepath = self.output_folder / filename
        
        # Save to file (Anki format: Question<tab>Answer<tab>Tags)
        with open(filepath, 'w', encoding='utf-8') as f:
            for card in flashcards:
                # Prepare tags including chapter and difficulty
                tags = list(card.tags) if card.tags else []
                tags.extend([
                    f"Source:{card.source}",
                    f"Difficulty:{card.difficulty}" if card.difficulty else "Difficulty:Unknown",
                    f"Type:{card.card_type}",
                    f"Book:{book.title}"
                ])
                tag_string = ' '.join(tags)
                
                # Write in Anki import format
                f.write(f"{card.front}\t{card.back}\t{tag_string}\n")
        
        self.logger.info(f"Saved {len(flashcards)} flashcards to Anki format: {filepath}")
        return filepath
    
    def save_processing_summary(self, books: List[Book], all_flashcards: Dict[str, List[FlashCard]]) -> Path:
        """
        Save a summary of the flashcard generation process.
        
        Args:
            books: List of processed books
            all_flashcards: Dictionary mapping book titles to their flashcards
            
        Returns:
            Path to the saved summary file
        """
        filename = f"flashcard_generation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_folder / filename
        
        # Calculate totals
        total_flashcards = sum(len(cards) for cards in all_flashcards.values())
        
        summary = {
            "generation_summary": {
                "generated_at": datetime.now().isoformat(),
                "total_books": len(books),
                "total_chapters": sum(book.total_chapters for book in books),
                "total_flashcards": total_flashcards,
                "average_flashcards_per_book": total_flashcards / len(books) if books else 0
            },
            "books": [
                {
                    "title": book.title,
                    "author": book.author,
                    "chapters": book.total_chapters,
                    "flashcards_generated": len(all_flashcards.get(book.title, [])),
                    "words": book.total_word_count
                }
                for book in books
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved flashcard generation summary: {filepath}")
        return filepath
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be safe for use as a filename.
        
        Args:
            filename: The original filename string
            
        Returns:
            Sanitized filename string
        """
        # Replace unsafe characters with underscores
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # Remove extra spaces and limit length
        filename = filename.strip().replace(' ', '_')
        return filename[:100]  # Limit to 100 characters
