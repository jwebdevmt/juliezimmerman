from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript"}


def local_path(ref: str) -> str | None:
    parsed = urlsplit(ref)
    if parsed.scheme.casefold() in SKIP_SCHEMES or parsed.netloc:
        return None
    path = unquote(parsed.path)
    return path or None


def resolve_local(html_file: Path, ref: str, output_root: Path) -> tuple[Path | None, str | None]:
    path = local_path(ref)
    if path is None:
        return None, None

    root = output_root.resolve()
    if path.startswith("/"):
        target = root / path.lstrip("/")
    else:
        target = html_file.parent / path
    target = target.resolve()

    try:
        target.relative_to(root)
    except ValueError:
        return target, "reference escapes staged output"

    return target, None
