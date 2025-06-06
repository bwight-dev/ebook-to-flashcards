"""
PDF Parser module for extracting chapters from PDF books.

Uses PyMuPDF (fitz) for robust PDF text extraction and chapter detection.
"""

import fitz  # PyMuPDF
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from ..config.settings import AppConfig
from ..models.book import Book
from ..models.chapter import Chapter


@dataclass
class ChapterCandidate:
    """Helper class for potential chapter boundaries."""

    page_num: int
    text: str
    font_size: float
    font_name: str
    y_position: float


class PdfParsingError(Exception):
    """Custom exception for PDF parsing errors."""

    pass


class PdfParser:
    """
    Parser for PDF files that extracts chapters and converts them into our data models.

    Uses multiple strategies for chapter detection:
    1. Table of Contents (TOC) extraction
    2. Font-based heading detection
    3. Pattern-based chapter title recognition
    """

    def __init__(self, config: AppConfig):
        """
        Initialize the parser with configuration.

        Args:
            config: Application configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Common chapter patterns
        self.chapter_patterns = [
            r"^chapter\s+\d+",
            r"^ch\.\s*\d+",
            r"^\d+\.\s+[A-Z]",
            r"^part\s+\d+",
            r"^section\s+\d+",
            r"^\d+\s+[A-Z][a-z]+",  # "1 Introduction"
        ]

    def parse_pdf(self, pdf_path: Path) -> Book:
        """
        Parse a PDF file and return a Book object with chapters.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Book: Parsed book with metadata and chapters

        Raises:
            PdfParsingError: If the file cannot be read or parsed
        """
        if not pdf_path.exists():
            raise PdfParsingError(f"File not found: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path))

            # Extract metadata
            title = self._extract_title(doc, pdf_path)
            author = self._extract_author(doc)

            # Try multiple chapter detection strategies
            chapters = self._extract_chapters(doc)

            # Apply chapter limit if configured
            if self.config.max_chapters_per_book:
                chapters = chapters[: self.config.max_chapters_per_book]

            doc.close()

            return Book(
                title=title, author=author, file_path=str(pdf_path), chapters=chapters
            )

        except Exception as e:
            if isinstance(e, PdfParsingError):
                raise
            raise PdfParsingError(f"Failed to parse PDF {pdf_path}: {str(e)}")

    def _extract_title(self, doc, pdf_path: Path) -> str:
        """Extract book title from PDF metadata or filename."""
        metadata = doc.metadata
        if metadata.get("title"):
            return metadata["title"]

        # Fallback to filename
        return pdf_path.stem.replace("_", " ").replace("-", " ")

    def _extract_author(self, doc) -> str:
        """Extract author from PDF metadata."""
        metadata = doc.metadata
        if metadata.get("author"):
            return metadata["author"]
        return "Unknown Author"

    def _extract_chapters(self, doc) -> List[Chapter]:
        """
        Extract chapters using multiple detection strategies.

        Args:
            doc: PyMuPDF document object

        Returns:
            List[Chapter]: Detected chapters
        """
        # Strategy 1: Try TOC-based extraction
        chapters = self._extract_chapters_from_toc(doc)
        if chapters:
            self.logger.info(f"Found {len(chapters)} chapters using TOC")
            return chapters

        # Strategy 2: Font-based detection
        chapters = self._extract_chapters_by_font(doc)
        if chapters:
            self.logger.info(f"Found {len(chapters)} chapters using font detection")
            return chapters

        # Strategy 3: Pattern-based detection
        chapters = self._extract_chapters_by_pattern(doc)
        if chapters:
            self.logger.info(f"Found {len(chapters)} chapters using pattern detection")
            return chapters

        # Fallback: Split by pages in groups
        self.logger.warning(
            "No chapters detected, falling back to page-based splitting"
        )
        return self._extract_chapters_by_pages(doc)

    def _extract_chapters_from_toc(self, doc) -> List[Chapter]:
        """Extract chapters using the document's Table of Contents."""
        toc = doc.get_toc()
        if not toc:
            return []

        chapters = []
        chapter_boundaries = []

        # Find chapter-level entries in TOC
        for level, title, page in toc:
            if level <= 2:  # Usually chapters are level 1 or 2
                chapter_boundaries.append((page - 1, title))  # Convert to 0-based

        # Extract content between boundaries
        for i, (start_page, title) in enumerate(chapter_boundaries):
            end_page = (
                chapter_boundaries[i + 1][0]
                if i + 1 < len(chapter_boundaries)
                else doc.page_count
            )

            content = self._extract_text_from_pages(doc, start_page, end_page)
            if content.strip():
                chapters.append(
                    Chapter(
                        title=title,
                        content=content,
                        chapter_number=i + 1,
                        file_name=f"page_{start_page+1}_to_{end_page}.pdf",
                    )
                )

        return chapters

    def _extract_chapters_by_font(self, doc) -> List[Chapter]:
        """Detect chapters by analyzing font sizes and styles."""
        candidates = []

        # Analyze first few pages to find common heading patterns
        for page_num in range(min(10, doc.page_count)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if len(text) > 5 and self._looks_like_chapter_title(text):
                                candidates.append(
                                    ChapterCandidate(
                                        page_num=page_num,
                                        text=text,
                                        font_size=span["size"],
                                        font_name=span["font"],
                                        y_position=span["bbox"][1],
                                    )
                                )

        # Find the most common "heading" font characteristics
        if not candidates:
            return []

        # Group by font characteristics and find chapters
        heading_font_size = max(
            set(c.font_size for c in candidates),
            key=lambda x: sum(1 for c in candidates if c.font_size == x),
        )

        chapter_pages = [
            c.page_num for c in candidates if c.font_size >= heading_font_size - 1
        ]

        return self._create_chapters_from_pages(doc, chapter_pages, candidates)

    def _extract_chapters_by_pattern(self, doc) -> List[Chapter]:
        """Detect chapters using regex patterns."""
        chapter_starts = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split("\n")

            for line_num, line in enumerate(lines):
                line_clean = line.strip().lower()
                for pattern in self.chapter_patterns:
                    if re.match(pattern, line_clean, re.IGNORECASE):
                        chapter_starts.append((page_num, line.strip()))
                        break

        if not chapter_starts:
            return []

        # Create chapters from detected starts
        chapters = []
        for i, (start_page, title) in enumerate(chapter_starts):
            end_page = (
                chapter_starts[i + 1][0]
                if i + 1 < len(chapter_starts)
                else doc.page_count
            )

            content = self._extract_text_from_pages(doc, start_page, end_page)
            if content.strip():
                chapters.append(
                    Chapter(
                        title=title,
                        content=content,
                        chapter_number=i + 1,
                        file_name=f"chapter_{i+1}.pdf",
                    )
                )

        return chapters

    def _extract_chapters_by_pages(
        self, doc, pages_per_chapter: int = 10
    ) -> List[Chapter]:
        """Fallback method: split document into page-based chunks."""
        chapters = []

        for i in range(0, doc.page_count, pages_per_chapter):
            end_page = min(i + pages_per_chapter, doc.page_count)
            content = self._extract_text_from_pages(doc, i, end_page)

            if content.strip():
                chapters.append(
                    Chapter(
                        title=f"Section {len(chapters) + 1}",
                        content=content,
                        chapter_number=len(chapters) + 1,
                        file_name=f"pages_{i+1}_to_{end_page}.pdf",
                    )
                )

        return chapters

    def _extract_text_from_pages(self, doc, start_page: int, end_page: int) -> str:
        """Extract clean text from a range of pages."""
        text_parts = []

        for page_num in range(start_page, end_page):
            if page_num < doc.page_count:
                page = doc[page_num]
                text = page.get_text()

                # Clean up text
                text = self._clean_text(text)
                if text.strip():
                    text_parts.append(text)

        return "\n\n".join(text_parts)

    def _clean_text(self, text: str) -> str:
        """Clean extracted text for better readability."""
        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
        text = re.sub(r" +", " ", text)

        # Remove page numbers and headers/footers (common patterns)
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip likely headers/footers
            if (
                len(line) < 5
                or re.match(r"^\d+$", line)  # Page numbers
                or re.match(r"^page \d+", line.lower())
                or len(line.split()) == 1
                and line.isdigit()
            ):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _looks_like_chapter_title(self, text: str) -> bool:
        """Heuristic to determine if text looks like a chapter title."""
        text_lower = text.lower()

        # Common chapter indicators
        chapter_words = ["chapter", "part", "section", "introduction", "conclusion"]

        # Check patterns
        if any(word in text_lower for word in chapter_words):
            return True

        if re.match(r"^\d+\.?\s+[A-Z]", text):  # "1. Introduction" or "1 Introduction"
            return True

        # Title case and reasonable length
        if text.istitle() and 10 <= len(text) <= 100 and len(text.split()) <= 8:
            return True

        return False

    def _create_chapters_from_pages(
        self, doc, chapter_pages: List[int], candidates: List[ChapterCandidate]
    ) -> List[Chapter]:
        """Create chapter objects from detected page boundaries."""
        chapters = []
        chapter_pages = sorted(set(chapter_pages))

        for i, start_page in enumerate(chapter_pages):
            end_page = (
                chapter_pages[i + 1] if i + 1 < len(chapter_pages) else doc.page_count
            )

            # Find title for this chapter
            title = f"Chapter {i + 1}"
            for candidate in candidates:
                if candidate.page_num == start_page:
                    title = candidate.text
                    break

            content = self._extract_text_from_pages(doc, start_page, end_page)
            if content.strip():
                chapters.append(
                    Chapter(
                        title=title,
                        content=content,
                        chapter_number=i + 1,
                        file_name=f"chapter_{i+1}.pdf",
                    )
                )

        return chapters
