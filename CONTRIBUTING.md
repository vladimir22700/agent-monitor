# Contributing to Agent Monitor

Thank you for considering contributing to Agent Monitor! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, etc.)

### Suggesting Features

We love feature suggestions! Please open an issue with:
- Clear description of the feature
- Use case explaining why it's needed
- Example of how it would work

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code with Black (`black .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your fork (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/cogniolab/agent-monitor.git
cd agent-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,all]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy agent_monitor
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small
- Add tests for new features

### Areas We'd Love Help With

- Additional platform integrations (AutoGPT, LlamaIndex, etc.)
- Dashboard improvements
- Documentation
- Bug fixes
- Performance optimizations
- Test coverage improvements

## Questions?

Contact us at dev@cogniolab.com

Thank you for contributing! 🎉
