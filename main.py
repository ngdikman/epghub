"""
Backwards-compatible entry point: `python main.py [update|schedule]` is
the same as `epghub [update|schedule]`. Kept because existing Cloudflare
Pages builds run `poetry run python main.py`.
"""

import sys

from epg.cli import main

if __name__ == "__main__":
    sys.exit(main())
