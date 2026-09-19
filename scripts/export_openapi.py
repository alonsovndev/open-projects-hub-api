#!/usr/bin/env python3
"""
Export the live OpenAPI schema (generated from FastAPI route/Pydantic
annotations) to a static docs/api/openapi.json file.

This keeps a committable, CI-artifactable spec in sync with the code without
hand-authoring it — re-run whenever routes/DTOs change, or wire into CI.

Usage:
    python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path


# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.app import fastapi_app


OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "api" / "openapi.json"


def export_openapi() -> None:
    """Write the current OpenAPI schema to docs/api/openapi.json."""
    schema = fastapi_app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"✅ Exported OpenAPI schema ({len(schema['paths'])} paths) to {OUTPUT_PATH}")


if __name__ == "__main__":
    export_openapi()
