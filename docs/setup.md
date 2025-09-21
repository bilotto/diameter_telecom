# Installation

## Prerequisites

- Python 3.10 or higher
- pip package manager

## Installation Methods

### Prerequisites

Before installing diameter_telecom, you need to install the base diameter library:

```bash
# Install python-diameter from GitHub
pip install git+https://github.com/mensonen/diameter.git
```

### From Source (Recommended)

Since this package is not yet available on PyPI, you'll need to install it from the source:

```bash
git clone https://github.com/bilotto/diameter_telecom.git
cd diameter_telecom
pip install -e .
```

### Development Installation

For development work, install with development dependencies:

```bash
git clone https://github.com/bilotto/diameter_telecom.git
cd diameter_telecom
pip install -e ".[dev]"
```

### Documentation Installation

For building documentation, use the setup script:

**Windows:**
```bash
# Run the setup script
setup_docs.bat
```

**Linux/macOS:**
```bash
# Run the setup script
chmod +x setup_docs.sh
./setup_docs.sh
```

Or install manually:
```bash
# Install python-diameter
pip install git+https://github.com/mensonen/diameter.git

# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python] mkdocs-autorefs pymdown-extensions

# Install diameter_telecom
pip install -e .
```

## Dependencies

The library has the following dependencies:

### Core Dependencies
- **python-diameter**: Base diameter library for core Diameter protocol implementation
- **Python 3.10+**: Required Python version

### Development Dependencies (Optional)
- **pytest**: For running tests
- **black**: For code formatting

## Verification

After installation, verify the installation by running a simple test:

```python
from diameter_telecom import PCEF, PCRF, DataService
from diameter_telecom.diameter.constants import APP_3GPP_GX

# Test basic imports
print("Diameter Telecom installed successfully!")
```

## Docker Installation (Alternative)

If you prefer using Docker, you can use the provided Dockerfile:

```bash
# Build the Docker image
docker build -t diameter-telecom .

# Run with the image
docker run -it diameter-telecom
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're using Python 3.10+ and have installed the base diameter library
2. **Missing Dependencies**: Run `pip install -r requirements.txt` to install all required packages
3. **Permission Issues**: Use `pip install --user` if you encounter permission issues

### Getting Help

If you encounter issues during installation:

1. Check the [GitHub Issues](https://github.com/bilotto/diameter_telecom/issues) for known problems
2. Verify your Python version with `python --version`
3. Ensure all dependencies are properly installed

## Next Steps

After successful installation:

1. Check out the [User Guide](guide/index.md) to understand the architecture
2. Try the [comprehensive examples](examples/data_service_comprehensive.md) to see the library in action
3. Explore the [API Reference](api/services/data.md) for detailed documentation
