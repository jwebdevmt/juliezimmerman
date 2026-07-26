from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from builder.context import BuildContext, publish
from builder.validators.assets import validate_assets
from builder.validators.links import validate_links


class BuildPipelineTests(unittest.TestCase):
    def test_root_relative_links_and_assets_resolve_inside_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "assets" / "site.css").write_text("", encoding="utf-8")
            (root / "about.html").write_text("ok", encoding="utf-8")
            (root / "index.html").write_text(
                '<link href="/assets/site.css" rel="stylesheet">'
                '<a href="/about.html">About</a>',
                encoding="utf-8",
            )
            link_issues, link_count = validate_links(root)
            asset_issues, asset_count = validate_assets(root)
            self.assertEqual([], link_issues)
            self.assertEqual([], asset_issues)
            self.assertEqual(1, link_count)
            self.assertEqual(1, asset_count)

    def test_publish_replaces_complete_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            live = root / "docs"
            live.mkdir()
            (live / "old.txt").write_text("old", encoding="utf-8")
            stage = BuildContext(root / "stage")
            stage.prepare()
            (stage.output / "new.txt").write_text("new", encoding="utf-8")

            publish(stage, live)

            self.assertFalse((live / "old.txt").exists())
            self.assertEqual("new", (live / "new.txt").read_text(encoding="utf-8"))
            self.assertFalse((root / "docs-backup").exists())


if __name__ == "__main__":
    unittest.main()
