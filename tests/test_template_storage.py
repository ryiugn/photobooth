import pytest
from pathlib import Path
from datetime import datetime
import json
import os
import shutil

from src.template_storage import Template, TemplateStorage


@pytest.fixture
def temp_templates_dir(tmp_path):
    """Create a temporary templates directory for testing."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    yield templates_dir
    # Cleanup happens automatically with tmp_path


def test_template_requires_four_frames(temp_templates_dir):
    """Test that Template validation requires exactly 4 frame paths."""
    # Should raise ValueError with fewer than 4 frames
    with pytest.raises(ValueError, match="exactly 4 frame paths"):
        Template(name="test", frame_paths=["a", "b", "c"], created="2024-01-01T00:00:00")

    # Should raise ValueError with more than 4 frames
    with pytest.raises(ValueError, match="exactly 4 frame paths"):
        Template(name="test", frame_paths=["a", "b", "c", "d", "e"], created="2024-01-01T00:00:00")

    # Should accept exactly 4 frames
    template = Template(
        name="valid",
        frame_paths=["frame1.png", "frame2.png", "frame3.png", "frame4.png"],
        created="2024-01-01T00:00:00"
    )
    assert len(template.frame_paths) == 4


def test_save_and_load_template(temp_templates_dir):
    """Test that saving and loading a template preserves all data."""
    storage = TemplateStorage(templates_dir=str(temp_templates_dir))

    # Create a template
    template = Template(
        name="My Favorite Frames",
        frame_paths=[
            "project_files/frames/frame_simple.png",
            "project_files/frames/frame_kawaii.png",
            "project_files/frames/frame_classic.png",
            "project_files/frames/frame_simple.png"
        ],
        created="2024-01-15T10:30:00"
    )

    # Save the template
    saved_path = storage.save(template)
    assert saved_path is not None
    assert Path(saved_path).exists()

    # Load all templates
    loaded_templates = storage.load_all()

    # Should have exactly one template
    assert len(loaded_templates) == 1

    # Verify all fields match
    loaded = loaded_templates[0]
    assert loaded.name == "My Favorite Frames"
    assert len(loaded.frame_paths) == 4
    assert loaded.frame_paths[0] == "project_files/frames/frame_simple.png"
    assert loaded.frame_paths[1] == "project_files/frames/frame_kawaii.png"
    assert loaded.frame_paths[2] == "project_files/frames/frame_classic.png"
    assert loaded.frame_paths[3] == "project_files/frames/frame_simple.png"
    assert loaded.created == "2024-01-15T10:30:00"


def test_delete_template(temp_templates_dir):
    """Test that deleting a template removes its file."""
    storage = TemplateStorage(templates_dir=str(temp_templates_dir))

    # Create and save a template
    template = Template(
        name="To Be Deleted",
        frame_paths=["a", "b", "c", "d"],
        created="2024-01-01T00:00:00"
    )
    saved_path = storage.save(template)
    assert Path(saved_path).exists()

    # Delete the template
    storage.delete(template)

    # File should be deleted
    assert not Path(saved_path).exists()

    # Load all should return empty list
    loaded = storage.load_all()
    assert len(loaded) == 0


def test_load_all_sorts_by_created_date_newest_first(temp_templates_dir):
    """Test that load_all returns templates sorted by created date (newest first)."""
    storage = TemplateStorage(templates_dir=str(temp_templates_dir))

    # Create templates with different timestamps
    template1 = Template(
        name="Old",
        frame_paths=["a", "b", "c", "d"],
        created="2024-01-01T00:00:00"
    )
    template2 = Template(
        name="New",
        frame_paths=["e", "f", "g", "h"],
        created="2024-01-15T12:00:00"
    )
    template3 = Template(
        name="Middle",
        frame_paths=["i", "j", "k", "l"],
        created="2024-01-10T08:00:00"
    )

    # Save in random order
    storage.save(template1)
    storage.save(template3)
    storage.save(template2)

    # Load should return sorted by created date (newest first)
    loaded = storage.load_all()
    assert len(loaded) == 3
    assert loaded[0].name == "New"
    assert loaded[1].name == "Middle"
    assert loaded[2].name == "Old"


def test_load_all_handles_corrupted_json_gracefully(temp_templates_dir):
    """Test that load_all skips corrupted JSON files instead of crashing."""
    storage = TemplateStorage(templates_dir=str(temp_templates_dir))

    # Create a valid template
    valid_template = Template(
        name="Valid",
        frame_paths=["a", "b", "c", "d"],
        created="2024-01-01T00:00:00"
    )
    storage.save(valid_template)

    # Create a corrupted JSON file
    corrupted_file = temp_templates_dir / "corrupted_template.json"
    corrupted_file.write_text("{ invalid json content")

    # Load all should skip corrupted file and return only valid template
    loaded = storage.load_all()
    assert len(loaded) == 1
    assert loaded[0].name == "Valid"


def test_template_uses_safe_filename(temp_templates_dir):
    """Test that save() creates safe filenames from template names."""
    storage = TemplateStorage(templates_dir=str(temp_templates_dir))

    # Template name with unsafe characters
    template = Template(
        name="My Cool Template/With:Unsafe*Characters?",
        frame_paths=["a", "b", "c", "d"],
        created="2024-01-01T00:00:00"
    )

    saved_path = storage.save(template)

    # Filename should be safe (no special characters)
    assert "my_cool_template_with_unsafe_characters" in saved_path
    assert saved_path.endswith(".json")
    assert Path(saved_path).exists()
