"""Script to download, modify, and save SVG icons for the changelog."""

from pathlib import Path
import xml.etree.ElementTree as ET
import requests

# Define icon URLs and colors
ICONS = {
    "issue": {
        "url": "https://raw.githubusercontent.com/primer/octicons/main/icons/issue-opened-16.svg",
        "color": "#28a745",
    },
    "pull-request": {
        "url": "https://raw.githubusercontent.com/primer/octicons/main/icons/git-pull-request-16.svg",
        "color": "#6f42c1",
    },
    "commit": {
        "url": "https://raw.githubusercontent.com/primer/octicons/main/icons/git-commit-16.svg",
        "color": "#0366d6",
    },
    "comment": {
        "url": "https://raw.githubusercontent.com/primer/octicons/main/icons/comment-16.svg",
        "color": "#24292e",
    },
}


def download_svg(url: str) -> str:
    """Download SVG content from a URL."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


def modify_svg_color(svg_content: str, color: str) -> str:
    """Modify the SVG content to change its color."""
    root = ET.fromstring(svg_content)

    # Add fill attribute to the root svg element
    root.set("fill", color)

    # Convert back to string
    return ET.tostring(root, encoding="unicode")


def save_svg(content: str, filename: str):
    """Save SVG content to a file."""
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    filepath = assets_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {filename}")


def main():
    """Main function to download, modify, and save SVG icons."""
    for name, info in ICONS.items():
        svg_content = download_svg(info["url"])
        modified_svg = modify_svg_color(svg_content, info["color"])
        save_svg(modified_svg, f"{name}-icon.svg")


if __name__ == "__main__":
    main()
