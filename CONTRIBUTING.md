# Contributing to EnterpriseRAG

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/EnterpriseRAG.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Follow the [Setup Guide](docs/Setup.md) to get the project running locally

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8. Use type hints.
- **TypeScript**: Use strict mode. Prefer `const` over `let`.
- **CSS**: Use Tailwind utility classes. Maintain the Pagani design system.

### Git Workflow

1. Create feature branches from `main`
2. Write descriptive commit messages
3. Keep PRs focused and small
4. Update documentation when adding features

### Testing

- Add backend tests for new API endpoints (`backend/tests/`)
- Ensure existing tests pass: `cd backend && python -m pytest tests/ -v`
- Test UI changes across breakpoints (375px, 768px, 1024px, 1440px)

### Non-Breaking Changes

> ⚠ **Critical Rule**: Do NOT modify existing functionality. Only ADD improvements.

- Keep all existing API signatures intact
- Don't change authentication flow
- Don't alter UI layouts without approval
- Add new features as additive layers

## Pull Request Process

1. Ensure all tests pass
2. Update relevant documentation in `/docs`
3. Add a clear description of changes
4. Reference any related issues
5. Request review from maintainers

## Reporting Issues

- Use GitHub Issues for bug reports
- Include reproduction steps
- Specify your OS and browser version
- Attach screenshots for UI issues
