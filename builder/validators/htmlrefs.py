from __future__ import annotations

from html.parser import HTMLParser


class ReferenceParser(HTMLParser):
    """Collect link and asset references from generated HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.assets: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {name.casefold(): value for name, value in attrs if value is not None}
        tag = tag.casefold()

        href = values.get("href")
        src = values.get("src")

        if tag == "a" and href:
            self.links.append(href)
        elif tag == "link" and href:
            rel = {part.casefold() for part in values.get("rel", "").split()}
            if rel & {"stylesheet", "icon", "preload", "manifest"}:
                self.assets.append((href, "linked asset"))
        elif src:
            self.assets.append((src, f"{tag} source"))

        if tag == "video" and values.get("poster"):
            self.assets.append((values["poster"], "video poster"))

        srcset = values.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                ref = candidate.strip().split()[0] if candidate.strip() else ""
                if ref:
                    self.assets.append((ref, f"{tag} srcset"))

        if tag == "use" and href:
            self.assets.append((href, "SVG use target"))
