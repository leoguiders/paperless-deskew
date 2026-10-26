# paperless-deskew

Straightens skewed scanned pages for [paperless-ngx](https://docs.paperless-ngx.com/), with a focus on documents where paperless' built-in deskewing falls short, such as **sheet music**.

It has two parts:

- **Pre-consume hook**: runs inside paperless for every new document, regardless of its source (consume folder, web upload, e-mail, new versions), and straightens skewed pages before paperless processes them. The stored original is straight, not just the archive version.
- **Tag service** (optional, paperless-ngx 3.0+): straightens documents that are already in paperless. Tag a document with `begradigen` and it gets a straightened new version of itself.

## Why not paperless' own deskewing?

paperless deskews during OCR (`PAPERLESS_OCR_DESKEW`, on by default). In tests with sheet music it left a page skewed by 4° uncorrected and tilted a straight page by 0.6°. It is tuned for text lines, cannot be configured beyond on/off, and only affects the archive version; the original stays skewed.

## How it works

Projection profile: the page is binarised and rotated in small steps (±10°, coarse to fine down to 0.02°). For each angle the dark pixels per image row are summed. When text lines or staff lines are exactly horizontal, this row profile has sharp peaks; the angle with the highest variance wins.

- Pages without clear lines (photos, nearly empty pages) give a flat score curve and are left alone (`DESKEW_MIN_CONTRAST`).
- Each page of a PDF is handled separately; pages are only re-encoded if they actually were skewed.
- The page size and resolution are kept. Scanned PDFs are rebuilt from the page images (paperless then runs OCR on them); born-digital PDFs are never modified.
- The output is deterministic (same input, same bytes), which paperless needs to detect duplicates.

The correction is a rotation of the whole page. Warped copies or photos (different skew at the top and bottom) are corrected on average only; see [ROADMAP.md](ROADMAP.md).

## Setup

### 1. Run the container

The container copies the hook into a directory that paperless mounts, and runs the tag service.

```yaml
services:
  paperless-deskew:
    image: ghcr.io/<owner>/paperless-deskew:latest
    restart: unless-stopped
    environment:
      HOOK_DIR: /hooks
      PAPERLESS_URL: http://paperless:8000
      PAPERLESS_TOKEN: <API token>
    volumes:
      - ./hooks:/hooks
```

The hook directory is refreshed on every start, so `docker compose pull && docker compose up -d` also updates the hook.

### 2. Enable the hook in paperless

In the paperless-ngx compose file (webserver service):

```yaml
environment:
  PAPERLESS_PRE_CONSUME_SCRIPT: /usr/src/paperless/scripts/deskew_hook.py
  PAPERLESS_OCR_DESKEW: "false"
volumes:
  - /path/to/paperless-deskew/hooks:/usr/src/paperless/scripts:ro
```

If deskew is configured in the paperless UI (Settings -> Configuration -> OCR), switch it off there as well; that setting takes precedence over the environment variable.

The hook only uses libraries that the paperless image already contains (Pillow, pikepdf, img2pdf, numpy) and never blocks consumption: unsupported files, born-digital PDFs and errors leave the document unchanged. It logs one line per document to the paperless log (`deskew-hook: ...`).

Only one pre-consume script can be configured in paperless. If you already use one, call `deskew_hook.py` from it.

### 3. Straighten existing documents (tag service)

1. In the paperless web UI, add the tag `begradigen` to one or more documents (bulk edit works too).
2. Within a minute the service downloads the current original, straightens every skewed page and uploads the result as a **new version of the same document** (`POST /api/documents/{id}/update_version/`, paperless-ngx 3.0+). ID, title, tags, correspondent, custom fields and notes stay unchanged; paperless runs OCR on the new version, and the previous version remains available.
3. The tag is removed. If nothing was skewed, a note says so. Documents that cannot be processed (e.g. born-digital PDFs) get the tag `begradigen-fehler` and a note with the reason.

Both tags are created automatically. The API token ("My profile" -> API auth token) needs permission to change the documents.

## Configuration

### Hook (environment of the paperless container)

| Variable | Default | Description |
|---|---|---|
| `DESKEW_MAX_ANGLE` | `10` | Search range in degrees |
| `DESKEW_MIN_CONTRAST` | `3` | Confidence threshold; raise it if photos get rotated |

### Container / tag service

| Variable | Default | Description |
|---|---|---|
| `HOOK_DIR` | – | Copy the hook (`deskew_hook.py`, `deskew.py`) into this directory on start |
| `PAPERLESS_URL` | – | Base URL of paperless-ngx; enables the tag service |
| `PAPERLESS_TOKEN` | – | paperless API token |
| `PAPERLESS_DESKEW_TAG` | `begradigen` | Tag that requests straightening |
| `PAPERLESS_DESKEW_ERROR_TAG` | `begradigen-fehler` | Tag set when a document cannot be straightened |
| `PAPERLESS_POLL_INTERVAL` | `60` | Seconds between checks for tagged documents |
| `DESKEW_MAX_ANGLE` / `DESKEW_MIN_CONTRAST` | `10` / `3` | As for the hook |
| `DESKEW_JPEG_QUALITY` | `90` | JPEG quality for re-encoded pages |
| `LOG_LEVEL` | `INFO` | |

Without `PAPERLESS_URL`/`PAPERLESS_TOKEN` the container only provides the hook.

## Files

| File | Purpose |
|---|---|
| `deskew.py` | Skew detection and correction for images, PDFs and image files |
| `deskew_hook.py` | paperless pre-consume hook |
| `service.py` | Tag service using the paperless REST API |
