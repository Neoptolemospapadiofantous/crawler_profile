# Profile Automation System

A modular, secure, and scalable system for automated profile management and web-based task execution.

## 🚀 Features

- **Profile Management**: Create and manage user profiles with human-like characteristics
- **Web Automation**: Automated task execution with anti-detection capabilities
- **Stealth Technology**: Proxy rotation, fingerprint prevention, and browser isolation
- **Task Scheduling**: Flexible task execution with dependency management
- **Security-First**: Encrypted credentials and secure configuration management

## 📋 Prerequisites

- Python 3.9+
- MySQL 8.0+
- Google Chrome Browser
- ChromeDriver (or other Selenium driver)
- Optionally set `CHROMEDRIVER_PATH` or pass `--driver-path` to specify the driver location
- ffmpeg

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


## 🎯 Quick Start

```bash
# Create a profile
pa-cli profile create --username testuser

# Run automation tasks
pa-cli task execute --profile-id 1 --task-type youtube-channel

# Generate videos
pa-cli video create --category cats

# Register a template
pa-cli template register templates/FunnyIntro

# If the package isn't installed, replace `pa-cli` with `python -m src.cli`
```

## 9GAG Video Creator

Generate templated videos from 9GAG posts. Run the script with Python and
provide your OpenAI API key via `--api-key`, the `OPENAI_API_KEY` environment
variable, or a `.env` file:

```bash
python scripts/ninegag_video_creator.py --category cats --count 5
```

## 9GAG Batch Uploader

The script `ninegag_batch_uploader.py` downloads videos from 9GAG,
applies a template with `ffmpeg` and then uploads the result using
Selenium. Generated videos are uploaded as **unlisted** on YouTube so
they are not publicly visible by default.

### Populating `templates/`

Create a directory under `templates/` for each template. It must contain
a `manifest.json` file and any asset files. A minimal manifest looks
like:

```json
{
  "name": "FunnyIntro",
  "channels": ["ChannelA"],
  "steps": []
}
```

### Editing `channels.yml`

`channels.yml` associates a channel name with a browser profile path and
the upload page. Example:

```yaml
ChannelA:
  profile: /path/to/channelA/profile
  upload_url: https://youtube.com/upload
```

### Example Invocation

```bash
python ninegag_batch_uploader.py --date 2025-06-11 --template FunnyIntro
```

### Troubleshooting

- **Missing Chrome profile** – verify that the path configured in
  `channels.yml` exists and points to a valid browser profile.
- **ffmpeg errors** – ensure `ffmpeg` is installed and available on your
  `PATH`. Run `ffmpeg -version` to confirm.
- **Missing ChromeDriver** – set the `CHROMEDRIVER_PATH` environment variable or pass
  `--driver-path` to point to your local driver binary.

## 📁 Project Structure

```
profile-automation-system/
├── src/                    # Main application code
│   ├── automation/        # Web automation tasks
│   ├── core/             # Core functionality
│   └── ninegag/          # 9GAG helpers
├── config/               # Configuration files
├── templates/            # Video templates
├── scripts/             # Setup and utility scripts
├── tests/               # Test suite
└── ninegag_batch_uploader.py  # Batch upload script
```

## 🔧 Configuration

Configuration files live in the `config/` directory. Copy `.env.example` to `.env` and update the values for your environment.

## 🧪 Testing

Run the Phase 1 test suite to confirm your environment and project setup:

```bash
./test-phase1.sh
```

The script validates that required tools are available and the repository is properly configured.

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
