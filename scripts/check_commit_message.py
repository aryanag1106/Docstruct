"""
Checks that a commit message's first line follows Conventional Commits
(https://www.conventionalcommits.org/): `<type>(optional scope): <description>`.

Used by .gitlab-ci.yml's commit-message-lint job, reading $CI_COMMIT_MESSAGE.
Also runnable standalone for local testing:

    python scripts/check_commit_message.py "feat: add invoice schema"
"""

from __future__ import annotations

import os
import re
import sys

CONVENTIONAL_COMMIT_RE = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+\))?: .+")


def check(message: str) -> bool:
    first_line = message.splitlines()[0] if message.splitlines() else ""
    return bool(CONVENTIONAL_COMMIT_RE.match(first_line))


def main() -> int:
    message = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CI_COMMIT_MESSAGE", "")
    first_line = message.splitlines()[0] if message.splitlines() else ""

    if check(message):
        print(f"OK: {first_line!r} follows Conventional Commits.")
        return 0

    print(f"Commit message does not follow Conventional Commits: {first_line!r}")
    print("Expected: <type>(optional scope): <description>")
    print("Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci")
    print("Example: feat: add invoice schema")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
