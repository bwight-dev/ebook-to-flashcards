# EPUB to Flashcards

A Python application that converts EPUB ebooks into flashcards using Test-Driven Development (TDD) principles and clean architecture patterns.

## 🎯 Project Overview

This application reads EPUB files from an ebooks folder and processes them chapter by chapter to prepare content for flashcard generation. Built with a focus on maintainable, testable code following SOLID principles.

## 🏗️ Architecture

The project follows clean architecture principles with clear separation of concerns:

```
src/
├── models/          # Data models with Pydantic validation
├── config/          # Configuration management
├── parsers/         # EPUB parsing logic
└── services/        # Business logic orchestration
```

## ✅ Current Features

### Core Functionality
- **EPUB File Processing**: Reads and parses EPUB files using `ebooklib`
- **Chapter Extraction**: Converts HTML content to clean text using BeautifulSoup
- **Metadata Extraction**: Extracts book title, author, and chapter information
- **Data Validation**: Uses Pydantic models for type safety and validation
- **Configuration Management**: Environment-based settings with `pydantic-settings`

### Data Models
- **Chapter**: Title, content, word count (auto-calculated), chapter number, filename
- **Book**: Title, author, file path, chapters list, total word count (computed)

### Quality Assurance
- **93% Test Coverage**: Comprehensive test suite with 26 passing tests
- **TDD Development**: Built using Red-Green-Refactor cycles
- **Error Handling**: Custom exceptions and graceful error recovery
- **Logging**: Structured logging throughout the application

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ebook-to-flash-cards
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add EPUB files to the `ebooks/epub/` directory

### Usage

```bash
python main.py
```

The application will:
1. Scan the `ebooks/epub/` directory for EPUB files
2. Process each file to extract chapters
3. Display processing results and statistics

### Configuration

Create a `.env` file to customize settings:

```bash
EBOOKS_FOLDER_PATH=/custom/path/to/ebooks
MAX_CHAPTERS_PER_BOOK=50
LOG_LEVEL=INFO
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage report
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_epub_parser.py -v
```

Current test coverage: **93%** (26/26 tests passing)

## 📁 Project Structure

```
ebook-to-flash-cards/
├── main.py                           # Application entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── .gitignore                       # Git ignore patterns
├── ebooks/                          # Input EPUB files
│   └── epub/
├── output/                          # Generated output (future)
├── src/                             # Source code
│   ├── models/
│   │   ├── book.py                  # Book data model
│   │   └── chapter.py               # Chapter data model
│   ├── config/
│   │   └── settings.py              # Configuration management
│   ├── parsers/
│   │   └── epub_parser.py           # EPUB parsing logic
│   └── services/
│       └── book_processing_service.py # Business logic orchestration
└── tests/                           # Test suite
    ├── test_models.py               # Model tests
    ├── test_config.py               # Configuration tests
    ├── test_epub_parser.py          # Parser tests
    └── test_book_processing_service.py # Service tests
```

## 📊 Sample Output

Processing an EPUB file produces structured data like this:

```
Processing: How to Day Trade for a Living - Andrew Aziz
========================================
Chapters extracted: 39
Total words: 29,831
Average words per chapter: 765

Sample chapters:
- Chapter 1: An Introduction to Day Trading (1,234 words)
- Chapter 2: Don't Believe the Hype! (987 words)
- Chapter 3: Do You Have What It Takes? (1,456 words)
```

## 🔮 Next Steps

### Phase 1: Flashcard Generation
- [ ] Implement content analysis to identify key concepts
- [ ] Create question-answer pair generation algorithms
- [ ] Add support for different flashcard types (Q&A, cloze deletion, etc.)

### Phase 2: Persistence & Export
- [ ] Add database support for storing processed content
- [ ] Implement export functionality (JSON, CSV, Anki format)
- [ ] Create import/export for existing flashcard collections

### Phase 3: Advanced Features
- [ ] Web interface for managing flashcards
- [ ] Spaced repetition algorithm integration
- [ ] Machine learning for intelligent content extraction
- [ ] Support for additional ebook formats (PDF, MOBI)

### Phase 4: User Experience
- [ ] CLI improvements with progress bars and better formatting
- [ ] Configuration wizard for first-time setup
- [ ] Batch processing with parallel execution
- [ ] Content filtering and customization options

## 🛠️ Development

### Adding New Features

1. **Write Tests First**: Follow TDD principles
   ```bash
   # Create test file
   touch tests/test_new_feature.py
   # Write failing tests
   # Implement feature
   # Ensure tests pass
   ```

2. **Maintain Architecture**: Keep separation between models, services, and parsers

3. **Update Documentation**: Keep README and docstrings current

### Code Quality Standards

- Type hints for all function signatures
- Comprehensive docstrings following Google style
- Error handling with custom exceptions
- Logging for debugging and monitoring
- Test coverage above 90%

## 📦 Dependencies

Core dependencies:
- `ebooklib`: EPUB file parsing
- `pydantic`: Data validation and settings
- `beautifulsoup4`: HTML content extraction
- `pydantic-settings`: Environment-based configuration

Development dependencies:
- `pytest`: Testing framework
- `pytest-cov`: Coverage reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Implement the feature
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Troubleshooting

### Common Issues

**ModuleNotFoundError**: Ensure you're running from the project root and have installed dependencies

**EPUB parsing errors**: Check that EPUB files are valid and not corrupted

**Permission errors**: Ensure the application has read access to the ebooks directory

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 📈 Project Status

- ✅ **Core Architecture**: Complete with clean separation of concerns
- ✅ **EPUB Processing**: Robust parsing with error handling
- ✅ **Data Models**: Validated with Pydantic
- ✅ **Test Coverage**: 93% coverage with comprehensive test suite
- ⏳ **Flashcard Generation**: Planned for next phase
- ⏳ **Persistence Layer**: Planned for next phase
- ⏳ **Export Functionality**: Planned for next phase

**Current Version**: 0.1.0 (MVP - EPUB processing complete)
