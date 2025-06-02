"""
Test module for OpenAI flashcard generator.

Following TDD approach - write failing tests first, then implement the functionality.
Tests the OpenAI integration for generating flashcards from chapter content.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from src.models.chapter import Chapter
from src.models.flashcard import FlashCard


class TestOpenAIFlashcardGenerator:
    """
    TDD Cycle 1: OpenAI Flashcard Generator
    
    Testing the integration with OpenAI to generate flashcards from chapter content.
    """
    
    def test_openai_generates_flashcards(self):
        """Test OpenAI creates flashcards from chapter content"""
        # This will fail until we implement OpenAIFlashcardGenerator
        from src.services.openai_flashcard_generator import OpenAIFlashcardGenerator
        
        generator = OpenAIFlashcardGenerator("test-api-key")
        chapter = Chapter(
            title="Chapter 1: Day Trading Rules",
            content="Rule 1: Day trading is not a get-rich-quick strategy. You must treat it as a serious business.",
            chapter_number=1,
            file_name="chapter01.xhtml"
        )
        
        # Mock the OpenAI response
        with patch('src.services.openai_flashcard_generator.Runner') as mock_runner_class:
            mock_response = {
                "cards": [
                    {
                        "front": "What is Rule 1 of day trading?",
                        "back": "Day trading is not a get-rich-quick strategy",
                        "card_type": "basic",
                        "tags": ["rules", "mindset"],
                        "source": "Chapter 1: Day Trading Rules",
                        "difficulty": 1
                    }
                ]
            }
            
            # Mock the result object
            mock_result = MagicMock()
            mock_result.data = [MagicMock()]
            mock_result.data[-1].content = json.dumps(mock_response)
            
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_sync.return_value = mock_result
            mock_runner_class.return_value = mock_runner_instance
            
            cards = generator.generate_flashcards(chapter)
            
            assert len(cards) == 1
            assert cards[0].front == "What is Rule 1 of day trading?"
            assert cards[0].back == "Day trading is not a get-rich-quick strategy"
            assert cards[0].card_type == "basic"
            assert "rules" in cards[0].tags
            assert cards[0].source == "Chapter 1: Day Trading Rules"
            assert cards[0].difficulty == 1

    def test_openai_generator_initialization(self):
        """Test that the OpenAI generator initializes correctly with API key"""
        from src.services.openai_flashcard_generator import OpenAIFlashcardGenerator
        
        generator = OpenAIFlashcardGenerator("test-api-key")
        assert generator is not None
        assert hasattr(generator, 'agent')

    def test_openai_api_error_handling(self):
        """Test error handling when OpenAI API fails"""
        from src.services.openai_flashcard_generator import OpenAIFlashcardGenerator
        
        generator = OpenAIFlashcardGenerator("test-api-key")
        chapter = Chapter(
            title="Test Chapter",
            content="Test content",
            chapter_number=1,
            file_name="test.xhtml"
        )
        
        # Mock an API error
        with patch('src.services.openai_flashcard_generator.Runner') as mock_runner_class:
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_sync.side_effect = Exception("API Error")
            mock_runner_class.return_value = mock_runner_instance
            
            with pytest.raises(Exception) as exc_info:
                generator.generate_flashcards(chapter)
            
            assert "API Error" in str(exc_info.value)

    def test_openai_malformed_response_handling(self):
        """Test handling of malformed responses from OpenAI"""
        from src.services.openai_flashcard_generator import OpenAIFlashcardGenerator
        
        generator = OpenAIFlashcardGenerator("test-api-key")
        chapter = Chapter(
            title="Test Chapter",
            content="Test content",
            chapter_number=1,
            file_name="test.xhtml"
        )
        
        # Mock a malformed response
        with patch('src.services.openai_flashcard_generator.Runner') as mock_runner_class:
            mock_response = {"invalid": "response"}  # Missing 'cards' key
            
            mock_result = MagicMock()
            mock_result.data = [MagicMock()]
            mock_result.data[-1].content = json.dumps(mock_response)
            
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_sync.return_value = mock_result
            mock_runner_class.return_value = mock_runner_instance
            
            cards = generator.generate_flashcards(chapter)
            
            # Should return empty list when response is malformed
            assert cards == []

    def test_multiple_flashcards_generation(self):
        """Test generation of multiple flashcards from one chapter"""
        from src.services.openai_flashcard_generator import OpenAIFlashcardGenerator
        
        generator = OpenAIFlashcardGenerator("test-api-key")
        chapter = Chapter(
            title="Chapter 2: Trading Psychology",
            content="Psychology is crucial in trading. Fear and greed are the two main emotions that destroy traders. You must control your emotions to succeed.",
            chapter_number=2,
            file_name="chapter02.xhtml"
        )
        
        # Mock multiple cards response
        with patch('src.services.openai_flashcard_generator.Runner') as mock_runner_class:
            mock_response = {
                "cards": [
                    {
                        "front": "What are the two main emotions that destroy traders?",
                        "back": "Fear and greed",
                        "card_type": "basic",
                        "tags": ["psychology", "emotions"],
                        "source": "Chapter 2: Trading Psychology",
                        "difficulty": 2
                    },
                    {
                        "front": "Psychology is {{c1::crucial}} in trading",
                        "back": "crucial",
                        "card_type": "cloze",
                        "tags": ["psychology"],
                        "source": "Chapter 2: Trading Psychology", 
                        "difficulty": 1
                    }
                ]
            }
            
            mock_result = MagicMock()
            mock_result.data = [MagicMock()]
            mock_result.data[-1].content = json.dumps(mock_response)
            
            mock_runner_instance = MagicMock()
            mock_runner_instance.run_sync.return_value = mock_result
            mock_runner_class.return_value = mock_runner_instance
            
            cards = generator.generate_flashcards(chapter)
            
            assert len(cards) == 2
            assert cards[0].card_type == "basic"
            assert cards[1].card_type == "cloze"
            assert all(card.source == "Chapter 2: Trading Psychology" for card in cards)
