"""Install the portable LaTeX paper editor skill into an agent skill directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


SKILL_NAME = "latex-paper-editor"


def copy_skill(repository: Path, target_root: Path) -> Path:
    source = repository / "skills" / SKILL_NAME
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill file not found: {source / 'SKILL.md'}")
    destination = target_root.expanduser() / SKILL_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True, help="Agent skills directory")
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    destination = copy_skill(args.repository.resolve(), args.target)
    print(f"Installed {SKILL_NAME} at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
