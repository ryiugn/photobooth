"""
Frame Generator Script for Photobooth Application

This script generates sample frame PNG files with transparent centers
for the photobooth application.

Frame Specifications:
- Dimensions: 800x1000 pixels
- Photo area: 640x800 pixels (centered)
- Format: PNG with RGBA (supports transparency)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_simple_frame() -> Image.Image:
    """
    Create a simple pink frame with 'PHOTOBOOTH' text.

    Returns:
        PIL.Image: Frame image with transparent center
    """
    # Create image with RGBA mode for transparency
    img = Image.new('RGBA', (800, 1000), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw pink border (outer border)
    border_color = (255, 192, 203, 255)  # Pastel pink
    border_width = 10
    draw.rectangle(
        [(0, 0), (799, 999)],
        outline=border_color,
        width=border_width
    )

    # Draw inner rectangle border
    inner_border = 15
    draw.rectangle(
        [(inner_border, inner_border), (799 - inner_border, 999 - inner_border)],
        outline=border_color,
        width=5
    )

    # Draw "PHOTOBOOTH" text at bottom
    try:
        # Try to use a bold font
        font = ImageFont.truetype("arialbd.ttf", 48)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    text = "PHOTOBOOTH"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    # Center text at bottom
    text_x = (800 - text_width) // 2
    text_y = 920

    # Draw text with shadow for better visibility
    shadow_offset = 3
    draw.text(
        (text_x + shadow_offset, text_y + shadow_offset),
        text,
        fill=(51, 51, 51, 200),  # Dark gray shadow
        font=font
    )
    draw.text(
        (text_x, text_y),
        text,
        fill=(255, 255, 255, 255),  # White text
        font=font
    )

    return img


def create_kawaii_frame() -> Image.Image:
    """
    Create a kawaii-style frame with multiple borders and decorative elements.

    Returns:
        PIL.Image: Frame image with transparent center
    """
    img = Image.new('RGBA', (800, 1000), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw multiple pink borders for kawaii effect
    pink_light = (255, 192, 203, 255)  # Pastel pink
    pink_dark = (255, 182, 193, 255)   # Slightly darker pink

    # Outer thick border
    draw.rectangle([(0, 0), (799, 999)], outline=pink_light, width=20)

    # Second border
    draw.rectangle([(25, 25), (774, 974)], outline=pink_dark, width=10)

    # Third border
    draw.rectangle([(40, 40), (759, 959)], outline=pink_light, width=5)

    # Add decorative dots in corners
    dot_color = (255, 182, 193, 255)
    dot_positions = [
        (50, 50), (70, 50), (50, 70),  # Top-left corner
        (750, 50), (730, 50), (750, 70),  # Top-right corner
        (50, 950), (70, 950), (50, 930),  # Bottom-left corner
        (750, 950), (730, 950), (750, 930),  # Bottom-right corner
    ]

    for x, y in dot_positions:
        draw.ellipse([(x - 8, y - 8), (x + 8, y + 8)], fill=dot_color)

    # Add "✨ KAWAII ✨" text
    try:
        font = ImageFont.truetype("arialbd.ttf", 42)
    except:
        font = ImageFont.load_default()

    text = "✨ KAWAII ✨"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    text_x = (800 - text_width) // 2
    text_y = 920

    # Draw text with pink shadow
    draw.text(
        (text_x + 2, text_y + 2),
        text,
        fill=(255, 182, 193, 180),
        font=font
    )
    draw.text(
        (text_x, text_y),
        text,
        fill=(255, 255, 255, 255),
        font=font
    )

    return img


def create_classic_frame() -> Image.Image:
    """
    Create a classic dark frame with pink accent.

    Returns:
        PIL.Image: Frame image with transparent center
    """
    img = Image.new('RGBA', (800, 1000), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Draw dark charcoal border
    dark_gray = (51, 51, 51, 255)  # Charcoal gray
    draw.rectangle([(0, 0), (799, 999)], outline=dark_gray, width=25)

    # Draw pink inner accent
    pink_accent = (255, 192, 203, 255)
    draw.rectangle([(30, 30), (769, 969)], outline=pink_accent, width=8)

    # Draw second dark border
    draw.rectangle([(45, 45), (754, 954)], outline=dark_gray, width=5)

    # Add corner decorations
    corner_size = 40
    corners = [
        (45, 45, 45 + corner_size, 45 + corner_size),  # Top-left
        (754 - corner_size, 45, 754, 45 + corner_size),  # Top-right
        (45, 954 - corner_size, 45 + corner_size, 954),  # Bottom-left
        (754 - corner_size, 954 - corner_size, 754, 954),  # Bottom-right
    ]

    for corner in corners:
        draw.rectangle(corner, fill=pink_accent)

    # Add "CLASSIC" text
    try:
        font = ImageFont.truetype("arialbd.ttf", 48)
    except:
        font = ImageFont.load_default()

    text = "CLASSIC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    text_x = (800 - text_width) // 2
    text_y = 920

    # Draw text with elegant shadow
    draw.text(
        (text_x + 3, text_y + 3),
        text,
        fill=(51, 51, 51, 200),
        font=font
    )
    draw.text(
        (text_x, text_y),
        text,
        fill=(255, 192, 203, 255),  # Pink text
        font=font
    )

    return img


def main():
    """Main function to generate all frame files."""
    # Set up paths using pathlib for cross-platform compatibility
    base_dir = Path(__file__).parent.parent
    frames_dir = base_dir / "project_files" / "frames"

    # Create frames directory if it doesn't exist
    frames_dir.mkdir(parents=True, exist_ok=True)

    print("Generating frame files...")

    # Generate simple frame
    simple_frame = create_simple_frame()
    simple_path = frames_dir / "frame_simple.png"
    simple_frame.save(simple_path, "PNG")
    print(f"[OK] Created: {simple_path}")

    # Generate kawaii frame
    kawaii_frame = create_kawaii_frame()
    kawaii_path = frames_dir / "frame_kawaii.png"
    kawaii_frame.save(kawaii_path, "PNG")
    print(f"[OK] Created: {kawaii_path}")

    # Generate classic frame
    classic_frame = create_classic_frame()
    classic_path = frames_dir / "frame_classic.png"
    classic_frame.save(classic_path, "PNG")
    print(f"[OK] Created: {classic_path}")

    print("\n[SUCCESS] All frames generated successfully!")
    print(f"Frames directory: {frames_dir}")
    print(f"Total frames: 3")


if __name__ == "__main__":
    main()
