"""Intake configuration loader and validator."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import sys

try:
    import yaml
    from jsonschema import validate, ValidationError
except ImportError:
    print("Warning: pyyaml or jsonschema not installed. Run: pip install pyyaml jsonschema")
    sys.exit(1)


class IntakeConfig:
    """Loaded and validated intake configuration."""

    def __init__(self, data: Dict[str, Any], source_path: Optional[Path] = None):
        """Initialize intake config."""
        self.data = data
        self.source_path = source_path

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from config by key."""
        keys = key.split(".")
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        return self.data[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.data

    def to_dict(self) -> Dict[str, Any]:
        """Get raw dictionary."""
        return self.data


def load_schema() -> Dict[str, Any]:
    """Load the intake schema."""
    schema_path = Path(__file__).parent.parent.parent / "intake" / "schema" / "project_intake.schema.json"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path, 'r') as f:
        return json.load(f)


def load_intake_yaml(file_path: Path) -> IntakeConfig:
    """
    Load and validate intake YAML file.

    Args:
        file_path: Path to intake YAML file

    Returns:
        IntakeConfig object

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValidationError: If config doesn't match schema
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Intake file not found: {file_path}")

    # Load YAML
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    # Validate against schema
    schema = load_schema()
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise ValidationError(
            f"Intake validation failed: {e.message}\nPath: {list(e.path)}"
        ) from e

    return IntakeConfig(data, source_path=file_path)


def validate_intake(file_path: Path) -> tuple[bool, Optional[str]]:
    """
    Validate intake file without loading.

    Args:
        file_path: Path to intake YAML file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        load_intake_yaml(file_path)
        return (True, None)
    except Exception as e:
        return (False, str(e))


def get_template_path(template_type: str) -> Path:
    """
    Get path to starter template.

    Args:
        template_type: Template type (webapp, analytics, ml, etc.)

    Returns:
        Path to template file

    Raises:
        ValueError: If template type is unknown
    """
    base = Path(__file__).parent.parent.parent / "intake" / "templates"
    template_path = base / f"starter.{template_type}.yaml"

    if not template_path.exists():
        raise ValueError(
            f"Unknown template type: {template_type}. "
            f"Available templates: {list_templates()}"
        )

    return template_path


def list_templates() -> list[str]:
    """List available starter templates."""
    templates_dir = Path(__file__).parent.parent.parent / "intake" / "templates"

    if not templates_dir.exists():
        return []

    templates = []
    for f in templates_dir.glob("starter.*.yaml"):
        # Extract type from filename: starter.<type>.yaml
        template_type = f.stem.replace("starter.", "")
        templates.append(template_type)

    return sorted(templates)


if __name__ == "__main__":
    # Demo usage
    print("Available templates:")
    for tmpl in list_templates():
        path = get_template_path(tmpl)
        print(f"  - {tmpl}: {path}")

    # Validate a template
    print("\nValidating webapp template...")
    webapp_path = get_template_path("webapp")
    valid, error = validate_intake(webapp_path)
    if valid:
        print(f"  ✓ {webapp_path.name} is valid")
        config = load_intake_yaml(webapp_path)
        print(f"  Project name: {config.get('project.name')}")
        print(f"  Project type: {config.get('project.type')}")
    else:
        print(f"  ✗ Validation failed: {error}")
