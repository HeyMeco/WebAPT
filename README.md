# APT Repository Previewer

A web-based tool for browsing and searching APT repositories. This tool allows you to explore package repositories, view package information, and download packages directly from the browser.

## Features

- Browse APT repositories by entering the base URL
- View repository metadata including architectures and components
- Browse and search packages in the repository
- Support for both regular and gzipped (.gz) Packages files
  - Automatic fallback to gzipped version when regular Packages file is not available
  - Visual indicator in UI when gzipped version is being used
- Download packages directly from the repository
- Responsive UI for desktop and mobile devices
- Docker support for easy deployment
- GitHub Container Registry integration for automated builds

## Requirements

- Python 3.7+
- UV package manager (recommended) or pip
- Docker (optional, for containerized deployment)

## Installation

### Using UV (Recommended)

1. Install UV if you haven't already:
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/HeyMeco/WebAPT.git
   cd WebAPT
   ```

3. Run the setup script:
   ```bash
   ./run.sh
   ```

### Using pip

1. Clone the repository:
   ```bash
   git clone https://github.com/HeyMeco/WebAPT.git
   cd WebAPT
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode

```bash
python app.py
```

The application will be available at http://localhost:5000

### Environment Variables

The application supports the following environment variables:

- `APTREPO`: Set a default APT repository URL. When this is set, the UI will automatically use this repository and disable the URL input field.

Example:
```bash
APTREPO=https://apt.armbian.com python app.py
```

### Using Docker

1. Build the image:
   ```bash
   docker build -t webapt .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 webapt
   ```

   With environment variable:
   ```bash
   docker run -p 5000:5000 -e APTREPO=https://apt.armbian.com webapt
   ```

### Using GitHub Container Registry

The latest Docker image is available at `ghcr.io/HeyMeco/WebAPT`:

```bash
docker pull ghcr.io/HeyMeco/WebAPT:main
docker run -p 5000:5000 ghcr.io/HeyMeco/WebAPT:main
```

With environment variable:
```bash
docker run -p 5000:5000 -e APTREPO=https://apt.armbian.com ghcr.io/HeyMeco/WebAPT:main
```

## How It Works

1. Enter an APT repository base URL (e.g., https://apt.armbian.com/dists/noble)
2. The application fetches the Release file to get repository metadata
3. Select an architecture and component to view available packages
4. Use the search feature to find specific packages
5. Download packages directly from the repository

## Development

### Project Structure

```
WebAPT/
├── app.py              # Main Flask application
├── lib/                # Core functionality
│   ├── __init__.py
│   └── apt_parser.py   # APT repository parsing
├── static/             # Static assets
│   ├── script.js       # Client-side JavaScript
│   └── style.css       # Stylesheets
├── templates/          # HTML templates
│   └── index.html      # Main page template
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
└── run.sh             # Setup and run script
```

### Adding Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details 