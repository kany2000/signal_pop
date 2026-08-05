"""
Style management module for Signal Pop video generation.
Handles color themes, fonts, and other visual styling elements.
"""

import hashlib
from config import STYLE_THEMES, FONT_REGULAR, FONT_BOLD, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS


def get_style_for_date(date_str: str) -> dict:
    """
    Select a style theme based on the date string.
    Ensures consistent but varying style for different dates.

    Args:
        date_str: Date string in YYYYMMDD format

    Returns:
        Dictionary containing color theme values
    """
    # Use date string as seed for consistent but varying style
    seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
    return STYLE_THEMES[seed % len(STYLE_THEMES)]


def get_font_regular(size: int, bold: bool = False):
    """
    Get a font object with specified size and weight.

    Args:
        size: Font size in points
        bold: Whether to use bold variant

    Returns:
        PIL ImageFont object
    """
    try:
        from PIL import ImageFont

        font_path = FONT_BOLD if bold else FONT_REGULAR
        return ImageFont.truetype(font_path, size)
    except Exception:
        # Fallback to default font if custom font not available
        from PIL import ImageFont

        return ImageFont.load_default()


def get_video_resolution():
    """
    Get video resolution settings.

    Returns:
        Tuple of (width, height, fps)
    """
    return VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS


def get_style_metadata(date_str: str) -> dict:
    """
    Get style information for metadata/display purposes.

    Args:
        date_str: Date string in YYYYMMDD format

    Returns:
        Dictionary with style information
    """
    style = get_style_for_date(date_str)
    return {
        "theme_index": hashlib.md5(date_str.encode()).hexdigest()[:8],
        "bar_color": style["bar"],
        "accent_color": style["accent"],
        "subtitle_color": style["sub"],
        "font_regular": FONT_REGULAR,
        "font_bold": FONT_BOLD,
        "resolution": get_video_resolution(),
    }
