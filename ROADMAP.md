# Roadmap

## Dewarping sheet music

The current correction rotates the whole page. Warped photocopies and phone
photos have staff lines that are skewed differently across the page, or
curved, so a single angle only corrects them on average.

[muskew](https://github.com/BreezeWhite/muskew) (MIT, split off from the OMR
project oemer) dewarps sheet music: a neural network predicts staff lines,
the line segments are connected into full lines (linear regression,
interpolation between segments), and a per-column y-coordinate mapping
straightens them. Points to consider:

- Only meaningful for sheet music: detect it first (groups of five evenly
  spaced lines in the row profile) and leave other documents to the rotation.
- The model and its runtime are not part of the paperless image. Run the
  dewarping in this project's container and let the hook send pages there
  (HTTP), falling back to rotation if the service is unreachable.
- muskew is a small project without a PyPI release or documented Python API;
  use it as a reference rather than a dependency.
- A classical staff-line detector (morphological opening with a long
  horizontal kernel) may be good enough for scans and avoid the model.

## Ideas

- Detect 90°/180° rotation as well (paperless already does that via
  `PAPERLESS_OCR_ROTATE_PAGES`, so only if it fails on sheet music)
- Optional per-document opt-out (e.g. a tag that makes the hook skip a file)
- Unit tests with sample pages in CI
