#!/usr/bin/env python3
"""paperless-ngx pre-consume hook: straighten skewed scanned pages.

paperless runs this script for every document before processing it,
regardless of its source (consume folder, web upload, e-mail, new versions).
It needs deskew.py next to it and only uses libraries that the paperless
image already contains (Pillow, pikepdf, img2pdf, numpy).

Use it instead of paperless' own deskewing (PAPERLESS_OCR_DESKEW=false),
which works poorly on sheet music and only affects the archive version.

Configuration (environment of the paperless container, all optional):
  DESKEW_MAX_ANGLE     search range in degrees (default 10)
  DESKEW_MIN_CONTRAST  confidence threshold (default 3)

The hook never blocks consumption: on any problem the file stays unchanged.
Its output (one line per document) appears in the paperless log.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MIME = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".tif": "image/tiff", ".tiff": "image/tiff"}


def main():
    path = os.environ.get("DOCUMENT_WORKING_PATH", "")
    mime = MIME.get(os.path.splitext(path)[1].lower())
    if not path or not os.path.isfile(path) or not mime:
        return
    try:
        import deskew
    except Exception as e:  # missing module or library
        print(f"deskew-hook: not available ({e}) - document left unchanged")
        return

    name = os.path.basename(os.environ.get("DOCUMENT_SOURCE_PATH", path))
    try:
        with open(path, "rb") as f:
            data = f.read()
        res = deskew.deskew_file(
            data, mime, name,
            max_angle=float(os.environ.get("DESKEW_MAX_ANGLE", "10")),
            min_contrast=float(os.environ.get("DESKEW_MIN_CONTRAST", "3")))
    except deskew.Skip as e:
        print(f"deskew-hook: {name}: {e}")
        return
    except Exception as e:
        print(f"deskew-hook: {name}: error ({e}) - document left unchanged")
        return
    if res is None:
        print(f"deskew-hook: {name}: no skew detected")
        return

    new, _, _, angles = res
    tmp = path + ".deskew-tmp"
    with open(tmp, "wb") as f:
        f.write(new)
    os.replace(tmp, path)
    pages = ", ".join(f"p{n} {a:+.2f}°" for n, a in enumerate(angles, 1) if a is not None)
    print(f"deskew-hook: {name}: straightened {pages}")


if __name__ == "__main__":
    main()
    sys.exit(0)
