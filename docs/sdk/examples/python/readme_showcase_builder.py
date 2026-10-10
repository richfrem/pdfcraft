#!/usr/bin/env python3
"""Compatibility Forwarder for e2e_showcase_example.py.

Deprecated: Please invoke docs/sdk/examples/python/e2e_showcase_example.py directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Forward execution to e2e_showcase_example
from e2e_showcase_example import (  # type: ignore
    build_readme_showcase_document,
    create_artcraft_badge,
    main,
)

if __name__ == "__main__":
    main()
