# Contributing to cpln-py

Thank you for your interest in contributing to cpln-py! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- [PDM](https://pdm-project.org/en/latest/) for dependency management
- Git
- Make

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/cpln-py.git
   cd cpln-py
   ```

2. **Install Dependencies**
   ```bash
   make dev-install
   ```

3. **Set Up Environment Variables**
   Create a `.env` file in the project root:
   ```env
   CPLN_TOKEN=your_service_account_key_here
   CPLN_ORG=your_organization_name
   CPLN_BASE_URL=https://api.cpln.io  # Optional
   ```

## Development Workflow

### 1. Create a Branch

Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

### 2. Make Changes

- Follow the coding standards (see below)
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described

### 3. Run Tests

```bash
make test
```

### 4. Code Quality Checks

```bash
# Run linting and type checking
make lint

# Format code
make format
```

### 5. Submit a Pull Request

1. Push your changes to your fork
2. Create a Pull Request against the main repository
3. Fill out the PR template
4. Wait for review and address any feedback

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for all function parameters and return values
- Keep functions focused and small
- Write docstrings for all public functions and classes

### Code Organization

- Place new modules in appropriate directories under `src/cpln/`
- Keep related functionality together
- Use clear, descriptive names for files and functions

### Documentation

- Update docstrings when modifying code
- Keep README.md and other documentation up to date
- Document all public APIs
- Include examples in docstrings

### Testing

- Write unit tests for all new features
- Maintain test coverage
- Use pytest fixtures for test setup
- Mock external dependencies

## Pull Request Process

1. **Title and Description**
   - Use clear, descriptive titles
   - Reference related issues
   - Describe changes and their impact

2. **Code Review**
   - Address all review comments
   - Keep the PR focused and manageable
   - Update documentation as needed

3. **CI/CD Checks**
   - All tests must pass (`make test`)
   - Code must pass linting (`make lint`)
   - Documentation must be up to date

## Development Tools

### Available Commands

```bash
# Install dependencies
make dev-install    # Install development dependencies
make install       # Install production dependencies

# Development
make test         # Run tests
make lint         # Run linting and type checking
make format       # Format code
make docs         # Build and serve documentation
make clean        # Clean build artifacts and cache
```

## Version Management

- Use [Semantic Versioning](https://semver.org/)
- Update version in `pyproject.toml`
- Update CHANGELOG.md for all changes

## Documentation

### Building Documentation

```bash
make docs  # Builds and serves documentation locally
```

### Documentation Standards

- Use Markdown for all documentation
- Include code examples
- Keep documentation up to date with code changes
- Document all public APIs

## Getting Help

- Open an issue for bugs or feature requests
- Join our community discussions
- Check existing documentation

## License

By contributing to cpln-py, you agree that your contributions will be licensed under the project's [Apache License 2.0](LICENSE).
