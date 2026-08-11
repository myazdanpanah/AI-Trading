# Contributing to Crypto AI Signal Platform

Thank you for your interest in contributing to the Crypto AI Signal Platform! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Pull Request Process](#pull-request-process)
7. [Coding Standards](#coding-standards)
8. [Documentation](#documentation)

---

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please be respectful and inclusive in all interactions.

---

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/crypto-platform.git
cd crypto-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start services with Docker
docker-compose up -d postgres redis

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-indicator`
- `fix/signal-generation-bug`
- `docs/update-deployment-guide`
- `refactor/optimize-caching`

### Commit Messages

Follow conventional commits:
```
feat: add new RSI calculation method
fix: resolve signal generation timeout
docs: update API documentation
refactor: optimize database queries
test: add integration tests for feedback loop
```

---

## Testing

### Running Tests

```bash
# Backend tests
python manage.py test apps --verbosity=2

# Specific app tests
python manage.py test apps.signals --verbosity=2

# With coverage
coverage run --source='apps' manage.py test apps
coverage report -m

# Frontend tests
cd frontend
npm test
```

### Test Requirements

- All new features must include tests
- Bug fixes must include regression tests
- Maintain or improve code coverage
- Tests should be fast and reliable

---

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update changelog.md** with your changes
5. **Request review** from maintainers

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Changelog updated
```

---

## Coding Standards

### Python (Backend)

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep functions focused and small
- Use meaningful variable names

```python
def calculate_signal_confidence(
    technical_score: float,
    sentiment_score: float,
    weights: Dict[str, float]
) -> float:
    """
    Calculate overall signal confidence from factor scores.
    
    Args:
        technical_score: Technical analysis score (0-100)
        sentiment_score: Sentiment analysis score (0-100)
        weights: Factor weights dictionary
    
    Returns:
        Weighted confidence score (0-100)
    """
    # Implementation here
    pass
```

### TypeScript (Frontend)

- Use strict TypeScript
- Prefer functional components with hooks
- Use meaningful component names
- Keep components small and focused

```typescript
interface SignalProps {
  symbol: string;
  confidence: number;
  onAction: (signal: Signal) => void;
}

export const SignalCard: React.FC<SignalProps> = ({
  symbol,
  confidence,
  onAction,
}) => {
  // Component implementation
};
```

### Django Best Practices

- Use class-based views when appropriate
- Prefer QuerySet methods over raw SQL
- Use `select_related` and `prefetch_related` for queries
- Handle errors gracefully

---

## Documentation

- Update README.md for major changes
- Add docstrings to new functions
- Update API documentation (OpenAPI/Swagger)
- Update DEPLOYMENT.md if deployment changes
- Update CHANGELOG.md with all changes

---

## Questions?

If you have questions, feel free to:
- Open an issue
- Start a discussion
- Reach out to maintainers

Thank you for contributing!
