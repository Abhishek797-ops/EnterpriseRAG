# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅        |
| 1.x     | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

1. Email the maintainers with details of the vulnerability
2. Include steps to reproduce the issue
3. Provide any proof-of-concept if applicable

### What to Expect

- Acknowledgment within 48 hours
- Status update within 5 business days
- Fix and disclosure within 30 days for critical issues

## Security Measures

This project implements:

- **JWT Authentication** with access + refresh token rotation
- **bcrypt password hashing** (cost factor 12)
- **Rate limiting** on all auth and chat endpoints
- **Input validation** via Pydantic with length limits
- **Security headers** (X-Content-Type-Options, X-Frame-Options, CSP, etc.)
- **Request size limiting** (1MB max body)
- **CORS restrictions** (localhost only in development)
- **Frontend input sanitization** (HTML tag stripping, XSS prevention)

## Best Practices for Deployment

- Use strong, unique values for `JWT_SECRET_KEY` and `JWT_REFRESH_SECRET_KEY`
- Never commit `.env` files with real secrets
- Use PostgreSQL in production (not SQLite)
- Enable HTTPS in production
- Restrict CORS origins to your actual domain
- Consider httpOnly cookies instead of localStorage for tokens
