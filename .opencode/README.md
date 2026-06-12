# .opencode Configuration

This directory contains OpenCode-specific configuration and knowledge base for AI-assisted development.

## 📁 Structure

```
.opencode/
├── README.md                    # This file
├── AGENTS.repo.md               # Repository-specific agent instructions
├── knowledge/
│   ├── repo-standards.md        # Detailed coding standards and patterns
│   ├── quick-reference.md       # Fast lookup for common commands and patterns
│   └── common-tasks.md          # Step-by-step guides for common tasks
├── package.json                 # OpenCode plugin dependencies
└── node_modules/                # OpenCode plugin installation
```

## 🎯 Purpose

This configuration helps AI agents understand:
- Repository structure and architecture
- Coding standards and conventions
- Common commands and workflows
- Step-by-step guides for frequent tasks

## 📚 Knowledge Files

### `AGENTS.repo.md`
High-level instructions loaded on every agent interaction. Contains:
- Domain boundaries (features, composition, shared)
- Build, test, and run commands
- Quality verification workflow
- Environment configuration

### `knowledge/repo-standards.md`
Detailed implementation standards. Contains:
- Clean code practices (use cases, DTOs, routes)
- Dependency injection patterns
- Repository patterns
- Validation patterns
- Import conventions
- Refactoring guidelines

### `knowledge/quick-reference.md` (NEW)
Fast lookup guide. Contains:
- Common commands (dev, test, quality, docker)
- Feature structure overview
- Dependency injection patterns
- Use case patterns
- File locations
- Testing patterns
- Environment variables
- Code review checklist

### `knowledge/common-tasks.md` (NEW)
Step-by-step task guides. Contains:
- Add a new endpoint
- Add a new database field
- Add a new repository method
- Add tests for existing code
- Add authorization checks
- Update API documentation
- Debug common issues

## 🔧 Configuration

The root `opencode.json` references these files:

```json
{
  "instructions": [
    "./AGENTS.md",
    "./.opencode/knowledge/repo-standards.md",
    "./.opencode/knowledge/quick-reference.md",
    "./.opencode/knowledge/common-tasks.md"
  ]
}
```

## 🚀 Usage

### For Developers

**Quick lookup:**
- Need a command? Check `quick-reference.md`
- Need step-by-step guide? Check `common-tasks.md`
- Need detailed patterns? Check `repo-standards.md`

**When asking AI for help:**
- AI automatically loads these instructions
- Reference specific patterns: "Follow the use case pattern from repo-standards"
- Reference specific tasks: "Follow the 'Add a new endpoint' guide"

### For AI Agents

These files are automatically loaded via `opencode.json` instructions. Priority:

1. **AGENTS.repo.md** - Always loaded first (high-level)
2. **repo-standards.md** - Detailed standards
3. **quick-reference.md** - Fast lookups
4. **common-tasks.md** - Step-by-step guides

## ✏️ Updating

### When to update?

- Architecture changes (new layers, boundaries)
- New coding patterns emerge
- Common pain points identified
- Frequently asked questions

### How to update?

1. Edit the relevant knowledge file
2. Keep it concise and practical
3. Include examples when possible
4. Update "Last Updated" timestamp
5. No need to restart agents (changes apply on next interaction)

### What to avoid?

- ❌ Duplicating global standards (those are in `~/.config/opencode/`)
- ❌ Writing long explanations (prefer examples)
- ❌ Including outdated information
- ❌ Contradicting other files

## 🎓 Best Practices

### Writing Instructions

**Do:**
- ✅ Use concrete examples
- ✅ Show both good and bad patterns
- ✅ Keep examples realistic
- ✅ Update when behavior changes

**Don't:**
- ❌ Write long theoretical explanations
- ❌ Include obvious information
- ❌ Duplicate documentation
- ❌ Use hypothetical examples

### File Organization

- **AGENTS.repo.md**: Quick overview (1-2 pages)
- **repo-standards.md**: Detailed patterns (5-10 pages)
- **quick-reference.md**: Fast lookups (5-10 pages)
- **common-tasks.md**: Step-by-step guides (10-20 pages)

## 🔗 Related Files

- `../AGENTS.md` - Repository agent instructions (symlink/import)
- `../opencode.json` - OpenCode configuration
- `../docs/` - Human-readable documentation

## 📝 Maintenance

**Regular reviews:**
- After major refactors
- When onboarding new developers
- Every 2-3 months

**Signs it needs updating:**
- AI suggests outdated patterns
- New developers ask same questions
- Recent code doesn't match standards

---

**Created:** June 11, 2026  
**Last Updated:** June 11, 2026
