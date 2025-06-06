"""
Application configuration settings.

Uses pydantic-settings for clean configuration management with
environment variable support and validation.
"""

from pathlib import Path
from typing import Optional, List
from pydantic import Field, field_validator, ConfigDict, SecretStr
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Application configuration with environment variable support.

    Environment variables can override defaults by using the same name
    in uppercase (e.g., EBOOKS_FOLDER, DEBUG_MODE).
    """

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    ebooks_folder: Path = Field(
        default=Path("./src/ebooks/epub"),
        description="Path to the folder containing EPUB files",
    )

    pdf_folder: Path = Field(
        default=Path("./src/ebooks/pdf"),
        description="Path to the folder containing PDF files",
    )

    output_folder: Path = Field(
        default=Path("./output"), description="Path to the folder for output files"
    )

    max_chapters_per_book: Optional[int] = Field(
        default=None,
        description="Maximum number of chapters to process per book (None for no limit)",
    )

    debug_mode: bool = Field(
        default=False, description="Enable debug mode for additional logging"
    )

    openai_api_key: Optional[SecretStr] = Field(
        default=None, description="OpenAI API key for generating flashcards"
    )

    # Supported file formats
    supported_formats: List[str] = Field(
        default=["epub", "pdf"], description="Supported ebook formats"
    )

    # PDF-specific settings
    pdf_pages_per_chapter: int = Field(
        default=10, description="Fallback: pages per chapter when no structure detected"
    )

    # Flashcard generation settings
    generate_flashcards: bool = Field(
        default=True, description="Whether to generate flashcards from chapters"
    )

    flashcards_per_chapter: int = Field(
        default=5, description="Target number of flashcards to generate per chapter"
    )

    flashcard_output_format: str = Field(
        default="json", description="Output format for flashcards (json, csv, anki)"
    )

    @field_validator("output_folder")
    @classmethod
    def create_output_folder(cls, v: Path) -> Path:
        """Ensure output folder exists, create if it doesn't."""
        output_path = Path(v)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    @field_validator("pdf_folder")
    @classmethod
    def create_pdf_folder(cls, v: Path) -> Path:
        """Ensure PDF folder exists, create if it doesn't."""
        pdf_path = Path(v)
        pdf_path.mkdir(parents=True, exist_ok=True)
        return pdf_path
