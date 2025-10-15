"""
Theme management API endpoints for client-specific branding.

Provides endpoints for:
- Listing client themes
- Loading/saving client themes
- Validating theme JSON against schema
- Merging base tokens with client overrides
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import jsonschema

router = APIRouter(prefix="/api/theme", tags=["theme"])

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLIENTS_DIR = PROJECT_ROOT / "clients"
SCHEMA_PATH = CLIENTS_DIR / ".schema" / "theme.schema.json"
BASE_TOKENS_PATH = PROJECT_ROOT / "design_system" / "tokens.json"


class ClientInfo(BaseModel):
    """Client metadata."""
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    name: str


class ColorOverrides(BaseModel):
    """Color overrides for a theme mode."""
    primary: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    emphasis: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    background: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    surface: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    text_secondary: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    border: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class Colors(BaseModel):
    """Color overrides for light and dark modes."""
    light: Optional[ColorOverrides] = None
    dark: Optional[ColorOverrides] = None


class Typography(BaseModel):
    """Typography overrides."""
    fontFamilyPrimary: Optional[str] = Field(None, pattern=r".*,\s*(sans-serif|serif|monospace)$")
    fontFamilyMonospace: Optional[str] = Field(None, pattern=r".*,\s*monospace$")
    fontSizeBase: Optional[str] = Field(None, pattern=r"^\d+px$")
    fontWeightNormal: Optional[int] = Field(None, ge=300, le=500)
    fontWeightBold: Optional[int] = Field(None, ge=600, le=800)


class Constraints(BaseModel):
    """Design constraints (must not violate Kearney brand)."""
    allowEmojis: bool = Field(False, const=True)
    allowGridlines: bool = Field(False, const=True)
    labelFirst: bool = Field(True, const=True)


class ClientTheme(BaseModel):
    """Client theme definition."""
    client: ClientInfo
    colors: Optional[Colors] = None
    typography: Optional[Typography] = None
    spacing: Optional[Dict[str, Any]] = None
    constraints: Constraints


@router.get("/clients")
async def list_clients():
    """
    List all available client themes.

    Returns:
        JSON with list of client slugs
    """
    try:
        CLIENTS_DIR.mkdir(parents=True, exist_ok=True)

        clients = []
        for client_dir in CLIENTS_DIR.iterdir():
            if client_dir.is_dir() and not client_dir.name.startswith("."):
                theme_file = client_dir / "theme.json"
                if theme_file.exists():
                    clients.append(client_dir.name)

        return {"clients": sorted(clients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list clients: {str(e)}")


@router.get("/clients/{slug}")
async def get_client_theme(slug: str):
    """
    Get theme for a specific client.

    Args:
        slug: Client identifier

    Returns:
        Client theme JSON
    """
    theme_path = CLIENTS_DIR / slug / "theme.json"

    if not theme_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme not found for client: {slug}")

    try:
        with open(theme_path, "r") as f:
            theme_data = json.load(f)
        return theme_data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON in theme file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load theme: {str(e)}")


@router.post("/clients/{slug}")
async def save_client_theme(slug: str, theme: ClientTheme):
    """
    Save theme for a specific client.

    Args:
        slug: Client identifier
        theme: Theme definition

    Returns:
        Success message
    """
    # Validate slug matches
    if theme.client.slug != slug:
        raise HTTPException(
            status_code=400,
            detail=f"Slug mismatch: URL slug '{slug}' does not match theme slug '{theme.client.slug}'"
        )

    # Create client directory
    client_dir = CLIENTS_DIR / slug
    client_dir.mkdir(parents=True, exist_ok=True)

    # Save theme
    theme_path = client_dir / "theme.json"
    try:
        with open(theme_path, "w") as f:
            json.dump(theme.dict(exclude_none=True), f, indent=2)

        return {
            "success": True,
            "message": f"Theme saved for client: {slug}",
            "path": str(theme_path.relative_to(PROJECT_ROOT))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save theme: {str(e)}")


@router.post("/validate")
async def validate_theme(theme: Dict[str, Any]):
    """
    Validate theme JSON against schema.

    Args:
        theme: Theme JSON to validate

    Returns:
        Validation result with errors if any
    """
    try:
        # Load schema
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)

        # Validate
        jsonschema.validate(instance=theme, schema=schema)

        return {
            "valid": True,
            "message": "Theme is valid",
            "errors": []
        }
    except jsonschema.ValidationError as e:
        return {
            "valid": False,
            "message": "Theme validation failed",
            "errors": [e.message]
        }
    except jsonschema.SchemaError as e:
        raise HTTPException(status_code=500, detail=f"Invalid schema: {str(e)}")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Theme schema not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/merge")
async def merge_theme(slug: str):
    """
    Merge base tokens with client theme overrides.

    Args:
        slug: Client identifier

    Returns:
        Merged token set
    """
    # Load base tokens
    try:
        with open(BASE_TOKENS_PATH, "r") as f:
            base_tokens = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Base tokens not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid base tokens JSON: {str(e)}")

    # Load client theme
    theme_path = CLIENTS_DIR / slug / "theme.json"
    if not theme_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme not found for client: {slug}")

    try:
        with open(theme_path, "r") as f:
            client_theme = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid theme JSON: {str(e)}")

    # Merge tokens (deep merge)
    merged = deep_merge(base_tokens, client_theme)

    return {
        "success": True,
        "client": slug,
        "tokens": merged
    }


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


@router.get("/schema")
async def get_theme_schema():
    """
    Get the theme JSON schema.

    Returns:
        JSON schema for client themes
    """
    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = json.load(f)
        return schema
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Theme schema not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid schema JSON: {str(e)}")


@router.delete("/clients/{slug}")
async def delete_client_theme(slug: str):
    """
    Delete theme for a specific client.

    Args:
        slug: Client identifier

    Returns:
        Success message
    """
    client_dir = CLIENTS_DIR / slug
    theme_path = client_dir / "theme.json"

    if not theme_path.exists():
        raise HTTPException(status_code=404, detail=f"Theme not found for client: {slug}")

    try:
        theme_path.unlink()

        # Remove directory if empty
        if not any(client_dir.iterdir()):
            client_dir.rmdir()

        return {
            "success": True,
            "message": f"Theme deleted for client: {slug}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete theme: {str(e)}")
