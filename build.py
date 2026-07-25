from __future__ import annotations

import argparse

from builder import legacy
from builder.site import build_all


def main() -> None:
    parser = argparse.ArgumentParser(description="Build juliezimmerman.me")
    parser.add_argument("--no-push", action="store_true", help="Build without offering to push")
    args = parser.parse_args()

    print("Loading config...")
    config = legacy.load_config()
    print("Loading content collections...")
    posts = legacy.load_posts()
    adaptive_pages = legacy.load_adaptive_pages()
    problem_pages = legacy.load_problem_pages()

    results = build_all(config, posts, adaptive_pages, problem_pages)
    total = sum(result.count for result in results)
    for result in results:
        print(f"  {result.collection}: {result.count}")
    print(f"Build complete. {total} artifact(s) generated in 'docs/'.")

    if args.no_push:
        print("Skipping push (--no-push).")
    elif legacy.ask_to_push():
        legacy.push()
    else:
        print("Skipping push. Site built locally.")


if __name__ == "__main__":
    main()
