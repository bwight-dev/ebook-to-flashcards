"""
OpenAI-powered flashcard generator.

This module provides functionality to generate flashcards from chapter content
using OpenAI's GPT models via the openai-agents SDK.
"""

import json
import logging
import os
from typing import List, Dict, Any
from agents import Agent, Runner
from src.models.chapter import Chapter
from src.models.flashcard import FlashCard


logger = logging.getLogger(__name__)


class OpenAIFlashcardGenerator:
    """
    Generates flashcards from chapter content using OpenAI's GPT models.
    
    This class uses the openai-agents SDK to interact with OpenAI's API
    and generate high-quality flashcards from book chapter content.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the OpenAI flashcard generator.
        
        Args:
            api_key: OpenAI API key for authentication
        """
        self.api_key = api_key
        
        # Set the API key as environment variable for the agents library
        os.environ['OPENAI_API_KEY'] = api_key
        
        self.agent = Agent(
            name="FlashcardCreator",
            instructions=self._get_instructions(),
            model="gpt-4o"
        )
    
    def _get_instructions(self) -> str:
        """
        Get the system instructions for the OpenAI agent.
        
        Returns:
            Detailed instructions for flashcard generation
        """
        return """You are an expert at creating educational flashcards.

TASK: Analyze book chapter content and create high-quality flashcards for student learning.

OUTPUT: Return valid JSON with this structure:
{
  "cards": [
    {
      "front": "Clear question",
      "back": "Concise answer", 
      "card_type": "basic|cloze|definition|qa",
      "tags": ["topic", "subtopic"],
      "source": "Chapter Title",
      "difficulty": 1-5
    }
  ]
}

CARD CREATION RULES:
1. Extract the most important concepts from the chapter
2. Focus on: rules, definitions, processes, examples, numbers
3. Create variety: 60% basic, 20% cloze, 15% definition, 5% complex QA
4. Use cloze format: "The maximum risk is {{c1::2%}} of account equity"
5. Include specific examples and numbers from text
6. Tag hierarchically: topic::subtopic::difficulty
7. Ensure questions are unambiguous and testable

QUALITY STANDARDS:
- Questions must have clear, single correct answers
- Avoid overly broad or subjective questions
- Include practical applications and examples
- Balance memorization with understanding
- Create reverse cards for key terms when appropriate"""

    def generate_flashcards(self, chapter: Chapter, num_flashcards: int = 5) -> List[FlashCard]:
        """
        Generate flashcards from a chapter using OpenAI.
        
        Args:
            chapter: Chapter object containing title and content
            num_flashcards: Number of flashcards to generate (default: 5)
            
        Returns:
            List of FlashCard objects generated from the chapter
            
        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Check if chapter content is suitable for flashcard generation
            if not self._is_suitable_for_flashcards(chapter):
                logger.info(f"Skipping chapter '{chapter.title}' - not suitable for flashcard generation")
                return []
            
            # Prepare the prompt for OpenAI
            prompt = f"""
Chapter Title: {chapter.title}

Chapter Content:
{chapter.content}

Please generate exactly {num_flashcards} flashcards from this chapter content following the instructions provided.
Focus on the most important concepts, definitions, and key points.
"""
            
            # Call OpenAI agent
            runner = Runner()
            result = runner.run_sync(self.agent, prompt)
            
            # Extract the response content
            response = self._extract_response_content(result)
            
            # Parse and validate response
            flashcards = self._parse_response(response, chapter.title)
            
            # Log the generated flashcards
            if flashcards:
                logger.info(f"✅ Generated {len(flashcards)} flashcards for chapter '{chapter.title}'")
                for i, card in enumerate(flashcards, 1):
                    logger.info(f"  Card {i}: {card.front[:60]}{'...' if len(card.front) > 60 else ''}")
                    logger.debug(f"    Front: {card.front}")
                    logger.debug(f"    Back: {card.back}")
                    logger.debug(f"    Type: {card.card_type}, Difficulty: {card.difficulty}")
            else:
                logger.warning(f"❌ No flashcards generated for chapter '{chapter.title}'")
            
            return flashcards
            
        except Exception as e:
            logger.error(f"Failed to generate flashcards: {str(e)}")
            raise e
    
    def _is_suitable_for_flashcards(self, chapter: Chapter) -> bool:
        """
        Check if a chapter is suitable for flashcard generation.
        
        Args:
            chapter: Chapter to evaluate
            
        Returns:
            True if suitable for flashcards, False otherwise
        """
        # Check content length - too short chapters are likely not educational content
        if len(chapter.content.strip()) < 200:
            return False
        
        # Check for common patterns that indicate non-educational content
        content_lower = chapter.content.lower()
        title_lower = chapter.title.lower()
        
        # Skip common non-content sections
        skip_patterns = [
            'copyright', 'disclaimer', 'acknowledgment', 'acknowledgement',
            'dedication', 'about the author', 'table of contents', 'index',
            'bibliography', 'references', 'endnotes', 'footnotes',
            'published by', 'all rights reserved', 'isbn',
            'visit us at', 'www.', 'http://', 'https://'
        ]
        
        # Skip if title suggests non-educational content
        skip_title_patterns = [
            'title page', 'cover', 'dedication', 'acknowledgment',
            'copyright', 'disclaimer', 'about', 'author'
        ]
        
        for pattern in skip_title_patterns:
            if pattern in title_lower:
                return False
        
        # Skip if content contains too many skip patterns
        skip_count = sum(1 for pattern in skip_patterns if pattern in content_lower)
        if skip_count >= 3:  # If 3 or more skip patterns found
            return False
        
        # Check content-to-noise ratio
        # If more than 30% of content is legal/copyright text, skip
        legal_patterns = ['©', 'copyright', 'all rights reserved', 'disclaimer', 'liability']
        legal_text_length = sum(len(pattern) for pattern in legal_patterns if pattern in content_lower)
        if legal_text_length / len(chapter.content) > 0.3:
            return False
        
        return True
    
    def _extract_response_content(self, result) -> Dict[str, Any]:
        """
        Extract response content from RunResult.
        
        Args:
            result: RunResult object from the agent
            
        Returns:
            Dictionary containing the response content
        """
        try:
            content_text = None
            
            # Method 1: Check for final_output attribute (this is where the content is!)
            if hasattr(result, 'final_output') and result.final_output:
                content_text = result.final_output
                logger.debug(f"Found final_output: {content_text[:200]}...")
            
            # Method 2: Check new_items for message content
            elif hasattr(result, 'new_items') and result.new_items:
                logger.debug(f"Found new_items: {len(result.new_items)}")
                for item in reversed(result.new_items):  # Check from latest
                    if hasattr(item, 'raw_item') and hasattr(item.raw_item, 'content'):
                        for content_item in item.raw_item.content:
                            if hasattr(content_item, 'text'):
                                content_text = content_item.text
                                logger.debug(f"Found text in new_items: {content_text[:200]}...")
                                break
                    if content_text:
                        break
            
            # Method 3: Legacy fallback methods
            elif hasattr(result, 'messages') and result.messages:
                last_message = result.messages[-1]
                if hasattr(last_message, 'content'):
                    content_text = last_message.content
            elif hasattr(result, 'content'):
                content_text = result.content
            elif isinstance(result, str):
                content_text = result
            
            if content_text:
                # Parse the content - it's likely wrapped in markdown code blocks
                if isinstance(content_text, str):
                    # Remove markdown code block markers if present
                    import re
                    
                    # Look for JSON wrapped in ```json...``` or ```...```
                    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1).strip()
                        logger.debug(f"Extracted JSON from code block: {json_content[:200]}...")
                        try:
                            return json.loads(json_content)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse extracted JSON: {e}")
                    
                    # Try direct JSON parsing
                    try:
                        return json.loads(content_text)
                    except json.JSONDecodeError:
                        # Look for any JSON object in the text
                        json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                        if json_match:
                            try:
                                return json.loads(json_match.group())
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse found JSON: {e}")
                        
                        logger.warning(f"No valid JSON found in content")
                        logger.debug(f"Raw content: {content_text}")
                
                return {"raw_content": content_text}
            
            # Fallback: return empty dict if we can't extract content
            logger.warning("Could not extract any content from RunResult")
            return {}
            
        except Exception as e:
            logger.error(f"Failed to parse response content: {e}")
            logger.debug(f"Full error details:", exc_info=True)
            return {}
    
    def _parse_response(self, response: Dict[str, Any], source_title: str) -> List[FlashCard]:
        """
        Parse OpenAI response and convert to FlashCard objects.
        
        Args:
            response: Raw response from OpenAI agent
            source_title: Title of the source chapter
            
        Returns:
            List of FlashCard objects
        """
        try:
            # Handle malformed responses
            if not isinstance(response, dict) or "cards" not in response:
                logger.warning("Malformed response from OpenAI, returning empty list")
                return []
            
            cards = []
            for card_data in response["cards"]:
                try:
                    # Create FlashCard object with validation
                    card = FlashCard(
                        front=card_data["front"],
                        back=card_data["back"],
                        card_type=card_data["card_type"],
                        tags=card_data.get("tags", []),
                        source=card_data.get("source", source_title),
                        difficulty=card_data.get("difficulty")
                    )
                    cards.append(card)
                except (KeyError, TypeError) as e:
                    logger.warning(f"Skipping malformed card data: {e}")
                    continue
            
            return cards
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return []
