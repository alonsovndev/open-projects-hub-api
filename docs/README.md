# Open Projects Hub API - Documentation

This directory contains comprehensive documentation for the Open Projects Hub API.

## 📁 Directory Structure

```
docs/
├── README.md                      # This file - documentation index
├── DEPLOYMENT.md                  # Production deployment guide
├── CODE_QUALITY.md                # Code quality tools and practices
├── SETUP_SUMMARY.md               # Installation overview
├── DATABASE_MIGRATIONS.md         # Alembic migration & rollback runbook, seed data
├── MIGRATION_GUIDE.md             # Code quality standards migration guide (Ruff, not DB)
├── api/                          # API documentation
│   ├── README.md                 # API overview
│   ├── api-contract.md           # Complete API endpoint reference
│   ├── authentication.md         # Auth endpoints and flows
│   └── errors.md                 # Error codes and responses
├── engineering/                  # Engineering principles and patterns
│   ├── README.md                 # Engineering overview
│   ├── clean-architecture.md     # Clean Architecture guide
│   ├── composition-root.md       # Composition Root details
│   ├── ddd-patterns.md           # DDD patterns
│   ├── design-principles.md      # Design principles
│   ├── async-patterns.md         # Async programming patterns
│   ├── logging-standards.md      # Logging standards
│   └── logging-implementation.md # Logging implementation guide
├── setup/                        # Setup and installation guides
│   ├── ADMIN_SETUP.md            # Admin setup guide
│   └── ADMIN_QUICK_REF.md        # Admin quick reference
├── testing/                      # Testing strategy and coverage
│   ├── coverage-strategy.md      # Coverage strategy
│   └── COVERAGE-QUICK-REF.md     # Coverage quick reference
├── security/                     # Security documentation
│   └── README.md                 # Security overview and practices
└── configuration/                # Configuration guides
    └── rate-limiting-strategy.md # Rate limiting strategy
```

## 📚 Quick Links

### Getting Started
- [Project Quick Start (run & build)](../README.md) - High-level overview to get started quickly
- [Admin Setup Guide](./setup/ADMIN_SETUP.md) - Comprehensive guide for setting up the admin environment
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment with Docker
- [Installation Summary](./SETUP_SUMMARY.md) - Overview of the installation process
- [Database Migrations](./DATABASE_MIGRATIONS.md) - Alembic commands, rollback procedure, backward-compatibility checklist, seed data
- [API Documentation](./api/README.md) - API endpoints, requests, and responses

### Engineering
- [Engineering Overview](./engineering/README.md) - Principles, patterns, and architectural guidelines
- [Clean Architecture](./engineering/clean-architecture.md) - Details on Clean Architecture implementation
- [Composition Root](./engineering/composition-root.md) - Understanding dependency injection
- [DDD Patterns](./engineering/ddd-patterns.md) - Domain-Driven Design patterns
- [Async Patterns](./engineering/async-patterns.md) - Asynchronous programming patterns

### Testing & Quality
- [Code Coverage Strategy](./testing/coverage-strategy.md) - How to ensure sufficient test coverage
- [Coverage Quick Reference](./testing/COVERAGE-QUICK-REF.md) - Quick coverage commands
- [Code Quality](./CODE_QUALITY.md) - Comprehensive guide for code quality tools and practices

### Security
- [Security Overview](./security/README.md) - Security features and practices
- [Rate Limiting Strategy](./configuration/rate-limiting-strategy.md) - Rate limiting configuration



## 🤝 Contributing

When adding documentation:

1. **Keep it practical** - Focus on "how" and "why", not "what"
2. **Use examples** - Code snippets and real scenarios
3. **Update this index** - Add links to new documents
4. **Link between docs** - Cross-reference related content
5. **Keep it current** - Update when implementation changes

## 📝 Documentation Standards

- Use Markdown format
- Include table of contents for long documents
- Use code blocks with syntax highlighting
- Include examples and use cases
- Link to source code when relevant
- Keep line length reasonable (~100 chars)
- Use relative links for internal references

## 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
