# python
import argparse
import logging

from bowler import Query

MAPPING = {
    "button_ALL_to_STAGE_1": "button_all_to_stage_1",
}


def run(dry_run: bool = True, root: str = ".") -> None:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("bowler").setLevel(logging.DEBUG)

    for old, new in MAPPING.items():
        logging.info(
            "Processing %s -> %s (dry_run=%s, root=%s)", old, new, dry_run, root
        )
        # Preview: interactive=False, write=False -> zeigt Diffs auf stdout
        # Apply:   interactive=False, write=True  -> schreibt Dateien
        Query(root).select_function(old).rename(new).execute(
            interactive=False, write=(not dry_run)
        )
        Query(root).select_method(old).rename(new).execute(
            interactive=False, write=(not dry_run)
        )
        Query(root).select_attribute(old).rename(new).execute(
            interactive=False, write=(not dry_run)
        )
        Query(root).select_var(old).rename(new).execute(
            interactive=False, write=(not dry_run)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rename functions/methods using Bowler"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (otherwise preview only)"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root path to search (default: .). Set to your package dir to avoid scanning `scripts/`",
    )
    args = parser.parse_args()

    # Erst Vorschau: python `scripts/rename_methods.py`
    # Zum Anwenden: python `scripts/rename_methods.py` --apply --root path/to/your/module
    run(dry_run=not args.apply, root=args.root)
