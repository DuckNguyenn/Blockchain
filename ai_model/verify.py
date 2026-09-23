from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_model.logging_service import verify_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify an HRC incident log hash")
    parser.add_argument("log", type=Path)
    args = parser.parse_args()

    payload = json.loads(args.log.read_text(encoding="utf-8"))
    valid = verify_sha256(payload)
    print("VALID: log matches its stored SHA-256 hash" if valid else "INVALID: log was changed")
    raise SystemExit(0 if valid else 1)


if __name__ == "__main__":
    main()
