# Canvas sizes, layout family and project folder per aspect ratio; capture/lib.py FORMATS uses the same keys.
import os

FORMATS = {"land": (1920, 1080), "port": (1080, 1920), "16x10": (1920, 1200), "4x3": (1440, 1080),
           "1x1": (1080, 1080), "4x5": (1080, 1350), "21x9": (2520, 1080)}
RATIO = {"land": "16x9", "port": "9x16"}


def layout_of(fmt):
    """The layout branch build.py uses: wide canvases follow 16:9, square and tall ones follow 9:16."""
    w, h = FORMATS[fmt]
    return "land" if w / h >= 1.3 else "port"


def project_dir(root, fmt):
    return os.path.join(root, "videos", f'{os.environ.get("FILM_NAME", "netigen-film")}-{RATIO.get(fmt, fmt)}')
