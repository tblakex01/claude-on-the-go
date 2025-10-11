#!/usr/bin/env python3
"""
Generate PWA icons for claude-on-the-go

Creates all required icon sizes with a simple, recognizable design.
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required")
    print("Install with: pip install Pillow")
    exit(1)


def create_icon(size: int, output_path: Path) -> None:
    """
    Create a square icon with gradient background and 'C' letter.

    Args:
        size: Icon size in pixels (square)
        output_path: Path to save the PNG file
    """
    # Create image with gradient background
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    # Draw gradient background (dark purple to dark blue)
    for y in range(size):
        # Interpolate between two colors
        ratio = y / size
        r = int(30 * (1 - ratio) + 20 * ratio)
        g = int(20 * (1 - ratio) + 30 * ratio)
        b = int(40 * (1 - ratio) + 60 * ratio)
        draw.rectangle([(0, y), (size, y + 1)], fill=(r, g, b))

    # Draw 'C' letter in center
    try:
        # Try to use a nice font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw 'C' with white color
    text = "C"

    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - bbox[1]

    # Draw text with slight shadow for depth
    shadow_offset = max(2, size // 100)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
    draw.text((x, y), text, font=font, fill=(255, 255, 255))

    # Add rounded corners for modern look (for larger icons)
    if size >= 192:
        # Create mask for rounded corners
        corner_radius = size // 8
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (size, size)], corner_radius, fill=255)

        # Apply mask
        output = Image.new("RGB", (size, size), (255, 255, 255))
        output.paste(img, (0, 0))
        img = output

    # Save PNG
    img.save(output_path, "PNG", optimize=True)
    print(f"✓ Created {output_path.name} ({size}x{size})")


def main():
    """Generate all PWA icon sizes"""
    # Icon sizes required for PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]

    # Also generate favicon sizes
    favicon_sizes = [16, 32]

    # Output directory
    output_dir = Path(__file__).parent.parent / "legacy" / "frontend" / "icons"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating PWA icons...")
    print()

    # Generate PWA icons
    for size in sizes:
        output_path = output_dir / f"icon-{size}x{size}.png"
        create_icon(size, output_path)

    # Generate favicon sizes
    for size in favicon_sizes:
        output_path = output_dir / f"icon-{size}x{size}.png"
        create_icon(size, output_path)

    # Generate apple-touch-icon (180x180 for iOS)
    apple_icon_path = output_dir / "apple-touch-icon.png"
    create_icon(180, apple_icon_path)

    print()
    print(f"✅ All icons generated successfully!")
    print(f"📁 Output directory: {output_dir}")
    print()
    print("Next steps:")
    print("1. Review icons: open legacy/frontend/icons/")
    print("2. Test PWA installation on mobile device")
    print("3. Run Lighthouse audit: npx lighthouse http://localhost:8001")


if __name__ == "__main__":
    main()
