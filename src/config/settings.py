"""
Application configuration settings.

Uses pydantic-settings for clean configuration management with
environment variable support and validation.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Application configuration with environment variable support.
    
    Environment variables can override defaults by using the same name
    in uppercase (e.g., EBOOKS_FOLDER, DEBUG_MODE).
    """
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    ebooks_folder: Path = Field(
        default=Path("./ebooks/epub"),
        description="Path to the folder containing EPUB files"
    )
    
    output_folder: Path = Field(
        default=Path("./output"),
        description="Path to the folder for output files"
    )
    
    max_chapters_per_book: Optional[int] = Field(
        default=None,
        description="Maximum number of chapters to process per book (None for no limit)"
    )
    
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode for additional logging"
    )
    
    @field_validator('output_folder')
    @classmethod
    def create_output_folder(cls, v: Path) -> Path:
        """Ensure output folder exists, create if it doesn't."""
        output_path = Path(v)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
