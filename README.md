# Profile Automation System

A modular, secure, and scalable system for automated profile management and web-based task execution.

## 🚀 Features

- **Profile Management**: Create and manage user profiles with human-like characteristics
- **Web Automation**: Automated task execution with anti-detection capabilities
- **Stealth Technology**: Proxy rotation, fingerprint prevention, and browser isolation
- **Task Scheduling**: Flexible task execution with dependency management
- **Security-First**: Encrypted credentials and secure configuration management

## 📋 Prerequisites

- Python 3.8+
- MySQL 8.0+
- Google Chrome Browser
- ChromeDriver

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/profile-automation-system.git
   cd profile-automation-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install in editable mode**
   ```bash
   pip install -e .
   ```

5. **Setup configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**
   ```bash
   python scripts/migrate.py
   ```

## 🎯 Quick Start

```bash
# Create a profile
pa-cli profile create --username testuser

# Run automation tasks
pa-cli task execute --profile-id 1 --task-type youtube-channel

# Generate videos
pa-cli video create --category cats

# If the package isn't installed, replace `pa-cli` with `python -m src.cli`
```

## 📁 Project Structure

```
profile-automation-system/
├── src/                    # Main application code
│   ├── core/              # Core functionality
│   ├── automation/        # Web automation tasks
│   ├── profiles/          # Profile management
│   ├── ui/               # User interfaces
│   └── utils/            # Utility functions
├── config/               # Configuration files
├── tests/               # Test suite
├── docs/                # Documentation
└── scripts/             # Setup and utility scripts
```

## 🔧 Configuration

See [Configuration Guide](docs/user-guide/configuration.md) for detailed setup instructions.

## 📚 Documentation

- [User Guide](docs/user-guide/README.md)
- [API Reference](docs/api/README.md)
- [Development Guide](docs/development/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is for educational and legitimate automation purposes only. Users are responsible for complying with all applicable laws and terms of service.
