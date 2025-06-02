"""
Test module for configuration management.

Following TDD approach - testing configuration settings that our application needs
to manage file paths, processing options, and other configurable parameters.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError


class TestAppConfig:
    """
    TDD Cycle 3: Configuration Management
    
    Testing configuration settings using pydantic-settings for clean
    environment variable handling and validation.
    """
    
    def test_default_config_creation(self):
        """
        RED: This test will fail because AppConfig doesn't exist yet.
        
        Testing that configuration can be created with sensible defaults.
        """
        from src.config.settings import AppConfig
        
        config = AppConfig()
        
        assert config.ebooks_folder == Path("./ebooks/epub")
        assert config.output_folder == Path("./output")
        assert config.max_chapters_per_book is None  # No limit by default
        assert config.debug_mode is False
    
    def test_config_with_custom_values(self):
        """
        Testing configuration with custom values provided.
        """
        from src.config.settings import AppConfig
        
        config = AppConfig(
            ebooks_folder="./custom/ebooks",
            output_folder="./custom/output", 
            max_chapters_per_book=10,
            debug_mode=True
        )
        
        assert config.ebooks_folder == Path("./custom/ebooks")
        assert config.output_folder == Path("./custom/output")
        assert config.max_chapters_per_book == 10
        assert config.debug_mode is True
    
    def test_config_validates_paths_exist(self):
        """
        Testing that configuration validates that required directories exist.
        """
        from src.config.settings import AppConfig
        
        # This should work with our actual ebooks folder
        config = AppConfig(ebooks_folder="./ebooks/epub")
        assert config.ebooks_folder.exists()
    
    def test_config_creates_output_folder_if_missing(self):
        """
        Testing that output folder is created if it doesn't exist.
        """
        from src.config.settings import AppConfig
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "new_output"
            config = AppConfig(output_folder=str(output_path))
            
            # Should create the directory
            assert config.output_folder.exists()
            assert config.output_folder.is_dir()
    
    def test_config_from_environment_variables(self):
        """
        Testing that configuration can be loaded from environment variables.
        """
        import os
        from src.config.settings import AppConfig
        
        # Set environment variables
        os.environ["EBOOKS_FOLDER"] = "./test/ebooks"
        os.environ["DEBUG_MODE"] = "true"
        os.environ["MAX_CHAPTERS_PER_BOOK"] = "5"
        
        try:
            config = AppConfig()
            
            assert config.ebooks_folder == Path("./test/ebooks")
            assert config.debug_mode is True
            assert config.max_chapters_per_book == 5
        finally:
            # Clean up environment variables
            for key in ["EBOOKS_FOLDER", "DEBUG_MODE", "MAX_CHAPTERS_PER_BOOK"]:
                os.environ.pop(key, None)
