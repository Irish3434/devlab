# Picture Finder

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Irish3434/devlab/workflows/CI/badge.svg)](https://github.com/Irish3434/devlab/actions)

A polished, professional Python application for detecting and managing duplicate images in large photo collections (up to 300,000+ files). Features perceptual hashing for accurate duplicate identification, automatic video separation, and user-configurable copy/move operations with timestamped filenames.

## Features

- **🔍 Duplicate Detection**: Uses `imagehash.average_hash` to detect near-duplicates with adjustable similarity threshold (1-20)
- **📹 Video Separation**: Automatically moves videos (>50MB or .mp4/.mov/.avi/.mkv) to separate folder
- **📁 Smart Organization**: Copy/move non-duplicates with timestamp-based naming to prevent overwrites
- **🚀 Performance Optimized**: Batch processing with configurable CPU/RAM usage modes
- **🎨 Polished GUI**: Responsive Tkinter interface with teal/white theme and accessibility features
- **📦 Export Capability**: ZIP export of unique photos with compression options
- **🌍 Internationalization**: Multi-language support (English, Spanish, French)
- **📊 Comprehensive Logging**: Detailed performance metrics and operation logs

## System Architecture

```mermaid
graph TD
    A[User] -->|Interacts with| B[GUI: interface.py]
    B -->|Configures & Runs| C[Core: image_processor.py]
    C -->|Hashes & Groups| D[File System: Scans Folder]
    C -->|Separates Videos| E[file_manager.py]
    E -->|Moves/Copies| F[unique_photos/ & videos/]
    C -->|Logs| G[log_writer.py]
    B -->|Exports ZIP| F
    G -->|Writes| H[Log File]
    style B fill:#ADD8E6,stroke:#008080
    style C fill:#ADD8E6,stroke:#008080
```

## Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Irish3434/devlab.git
   cd devlab/PictureFinder
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## Usage

1. **Select Folder**: Browse and select the folder containing your photos
2. **Configure Settings**: 
   - Adjust similarity threshold (default: 10)
   - Set batch size (default: 500)
   - Choose CPU/RAM usage mode
3. **Choose Action**: Select Copy or Move for non-duplicate files
4. **Process**: Click Run to start duplicate detection
5. **Export**: Optionally export unique photos as ZIP file

## Requirements

- **Python**: 3.12 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum (8GB+ recommended for large collections)
- **Storage**: Additional space equal to your photo collection size

## Project Structure

```
PictureFinder/
├── app.py                     # Main application entry point
├── requirements.txt           # Dependencies
├── setup.py                  # Package configuration
├── core/                     # Core functionality
│   ├── image_processor.py    # Duplicate detection and hashing
│   ├── file_manager.py       # File operations and video separation
│   └── log_writer.py         # Logging system
├── gui/                      # User interface
│   ├── interface.py          # Main GUI components
│   └── styles.py             # UI styling and theming
├── tests/                    # Unit tests
├── docs/                     # Documentation
├── assets/                   # Icons and localization files
└── .github/workflows/        # CI/CD configuration
```

## Development

### Local Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```bash
   pytest --cov
   ```

3. **Lint code:**
   ```bash
   pylint **/*.py
   ```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Performance

- **Small Collections** (<1,000 files): Processes in seconds
- **Medium Collections** (1,000-10,000 files): Processes in minutes
- **Large Collections** (10,000+ files): Optimized batching and multiprocessing

## Security

- Input validation and path sanitization
- No shell command execution
- Secure file operations with permission checks
- User-selected folder restrictions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 **Documentation**: See `docs/user_guide.md` for detailed instructions
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/Irish3434/devlab/issues)
- 💬 **Discussions**: Join discussions on [GitHub Discussions](https://github.com/Irish3434/devlab/discussions)

---

Made with ❤️ by the Picture Finder Team