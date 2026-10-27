# Canvas sizes, layout family, window and text zones per aspect ratio. Every script takes these keys.
import os

FORMATS = {"land": (1920, 1080), "port": (1080, 1920), "16x10": (1920, 1200), "4x3": (1440, 1080),
           "1x1": (1080, 1080), "4x5": (1080, 1350), "21x9": (2520, 1080)}
RATIO = {"land": "16x9", "port": "9x16"}


def layout_of(fmt):
    """Wide canvases follow 16:9, square and tall ones follow 9:16."""
    w, h = FORMATS[fmt]
    return "land" if w / h >= 1.3 else "port"


def project_dir(root, fmt):
    return os.path.join(root, "videos", f'{os.environ.get("FILM_NAME", "film")}-{RATIO.get(fmt, fmt)}')


def window_rect(fmt, look="fullbleed"):
    """(x, y, w, h) of the picture window. fullbleed fills the canvas; framed leaves room for titles and captions."""
    W, H = FORMATS[fmt]
    if look != "framed":
        return 0, 0, W, H
    if layout_of(fmt) == "land":
        x, y = round(W * 0.07), round(H * 0.08)
        return x, y, W - 2 * x, round(H * 0.74)
    x = round(W * 0.04)
    return x, round(H * 0.16), W - 2 * x, round(H * 0.56)


def zones(fmt):
    """Text placement: title (centred block), lower third, caption line; each (x, y, w, size[, max_words])."""
    W, H = FORMATS[fmt]
    m = min(W, H)
    land = layout_of(fmt) == "land"
    return {
        "title": (round(W * 0.08), round(H * (0.38 if land else 0.36)), round(W * 0.84), round(m * 0.085)),
        "lower": (round(W * 0.07), round(H * (0.80 if land else 0.70)), round(W * 0.86), round(m * 0.042)),
        "caption": (round(W * 0.06), round(H * (0.86 if land else 0.72)), round(W * 0.88), round(m * 0.044), 8 if land else 6),
    }
