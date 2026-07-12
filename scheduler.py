"""
Backwards-compatible entry point: `python scheduler.py` is the same as
`epghub schedule`. Kept because existing Docker images start the service
this way.
"""

import sys

from epg.cli import main

if __name__ == "__main__":
    sys.exit(main(["schedule"]))
