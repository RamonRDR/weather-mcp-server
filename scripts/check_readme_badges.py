"""Validate README badge parity against real pytest JUnit cases (no network or tokens)."""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

READMES = ("README.md", "README.pt-BR.md", "README.es.md")
COUNT_RE = re.compile(
    r"!\[pytest\]\(https://img\.shields\.io/badge/pytest-(\d+)%20passing-0A9EDC\)"
)
BADGE_RE = re.compile(r"!\[[^]]+\]\(([^)]+)\)")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_readme_badges.py <junit.xml>", file=sys.stderr)
        return 2

    root = ET.parse(sys.argv[1]).getroot()
    cases = list(root.iter("testcase"))
    if not cases:
        print("JUnit contains no testcase elements", file=sys.stderr)
        return 1
    failed = sum(
        any(child.tag in {"failure", "error"} for child in case)
        for case in cases
    )
    skipped = sum(any(child.tag == "skipped" for child in case) for case in cases)
    passed = len(cases) - failed - skipped
    inventories = []
    valid = failed == 0
    for filename in READMES:
        content = Path(filename).read_text(encoding="utf-8")
        match = COUNT_RE.findall(content)
        if match != [str(passed)]:
            print(
                f"{filename}: pytest badge {match}, expected exactly {passed} passing",
                file=sys.stderr,
            )
            valid = False
        badges = [
            url
            for url in BADGE_RE.findall(content)
            if "img.shields.io/badge/" in url or "/badge.svg?" in url
        ]
        if len(badges) != len(set(badges)):
            print(f"{filename}: duplicate badge URL", file=sys.stderr)
            valid = False
        inventories.append(badges)
    if not all(items == inventories[0] for items in inventories):
        print("README badge inventories differ between languages", file=sys.stderr)
        valid = False
    print(
        f"JUnit: {len(cases)} cases, {passed} passed, "
        f"{failed} failed, {skipped} skipped; "
        f"{len(inventories[0])} badges in each README"
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
