# YouTube Downloader Pro

A modern, feature-rich YouTube video downloader application with enhanced security, user management, and download capabilities.

## Features

### Authentication & Security
- Secure user authentication with bcrypt
- OAuth2 integration with Google
- Two-Factor Authentication (2FA) support
- JWT-based session management
- Password reset functionality
- Secure password storage

### Video Downloading
- Support for multiple video platforms (YouTube, Vimeo, Dailymotion)
- Multiple format options (mp4, webm, mkv)
- Quality selection (1080p, 720p, 480p, 360p)
- Audio extraction (mp3, wav, m4a, ogg)
- Playlist downloading
- Download queue management
- Progress tracking
- Download history

### Dashboard
- Download statistics and visualizations
- Download history with search and filtering
- Storage usage tracking
- Interactive charts
- Export functionality

### User Profile
- Profile picture management
- User preferences
- Download settings
- Security settings
- API key management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-downloader-pro.git
cd youtube-downloader-pro
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
- Copy `config.json.example` to `config.json`
- Update the configuration with your settings
- Set up MongoDB connection
- Configure OAuth2 credentials for Google login

5. Run the application:
```bash
python app.py
```

## Configuration

The application can be configured through the `config.json` file:

- `app`: Application settings (title, version, theme, etc.)
- `download`: Download settings (formats, qualities, paths)
- `database`: MongoDB connection settings
- `security`: Security settings (JWT, password requirements)
- `logging`: Logging configuration
- `cleanup`: File cleanup settings

## Requirements

- Python 3.8+
- MongoDB 4.4+
- FFmpeg (for audio extraction)
- Internet connection

## Dependencies

- customtkinter: Modern GUI framework
- pymongo: MongoDB driver
- bcrypt: Password hashing
- yt-dlp: Video downloading
- Pillow: Image processing
- requests: HTTP client
- python-jose: JWT handling
- python-dotenv: Environment variables
- google-auth: Google OAuth2
- pyotp: 2FA support
- qrcode: QR code generation
- matplotlib: Data visualization
- pandas: Data handling
- reportlab: PDF generation
- python-magic: File type detection
- ffmpeg-python: FFmpeg integration

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens are used for session management
- 2FA is available for additional security
- API keys and secrets are stored securely
- Regular security updates are recommended

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- yt-dlp team for the excellent video downloading library
- CustomTkinter team for the modern GUI framework
- All contributors and users of this project