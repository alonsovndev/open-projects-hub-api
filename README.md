# Open Projects Hub




## 🗄️ Database Management

### Initial Setup

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Configure Alembic to use your database URL
# Add this line to alembic/env.py (line 13):
config.set_main_option("sqlalchemy.url", get_postgres_database_url())
```

### Creating Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```