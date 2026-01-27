from dataclasses import dataclass
from typing import List
from pathlib import Path
import json
import re


@dataclass
class Template:
    """Represents a saved frame combination template."""
    name: str
    frame_paths: List[str]
    created: str

    def __post_init__(self):
        """Validate that exactly 4 frame paths are provided."""
        if len(self.frame_paths) != 4:
            raise ValueError(f"Template must have exactly 4 frame paths, got {len(self.frame_paths)}")


class TemplateStorage:
    """Manages saving, loading, and deleting frame templates."""

    def __init__(self, templates_dir: str = "project_files/templates"):
        """
        Initialize template storage.

        Args:
            templates_dir: Directory to store template JSON files
        """
        self.templates_dir = Path(templates_dir)
        # Create directory if it doesn't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save(self, template: Template) -> str:
        """
        Save a template to a JSON file.

        Args:
            template: Template object to save

        Returns:
            Absolute path to the saved file
        """
        # Generate safe filename from template name
        safe_name = self._make_safe_filename(template.name)
        filename = f"{safe_name}.json"
        filepath = self.templates_dir / filename

        # Convert template to dict
        template_dict = {
            "name": template.name,
            "frame_paths": template.frame_paths,
            "created": template.created
        }

        # Write to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template_dict, f, indent=2)

        return str(filepath.absolute())

    def load_all(self) -> List[Template]:
        """
        Load all templates from the templates directory.

        Returns:
            List of Template objects sorted by created date (newest first)
        """
        templates = []

        # Iterate through all JSON files in the templates directory
        for filepath in self.templates_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Create Template object from JSON data
                template = Template(
                    name=data["name"],
                    frame_paths=data["frame_paths"],
                    created=data["created"]
                )
                templates.append(template)
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue

        # Sort by created date (newest first)
        templates.sort(key=lambda t: t.created, reverse=True)
        return templates

    def delete(self, template: Template) -> None:
        """
        Delete a template's JSON file.

        Args:
            template: Template object to delete
        """
        # Generate safe filename from template name
        safe_name = self._make_safe_filename(template.name)
        filename = f"{safe_name}.json"
        filepath = self.templates_dir / filename

        # Delete file if it exists
        if filepath.exists():
            filepath.unlink()

    def _make_safe_filename(self, name: str) -> str:
        """
        Convert a template name to a safe filename.

        Args:
            name: Template name

        Returns:
            Safe filename with special characters replaced
        """
        # Convert to lowercase
        safe = name.lower()

        # Replace unsafe characters with underscores
        safe = re.sub(r'[^a-z0-9]+', '_', safe)

        # Remove leading/trailing underscores
        safe = safe.strip('_')

        return safe
