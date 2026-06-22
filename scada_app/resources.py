"""Resource path resolution that works both in development and when frozen.

PyInstaller unpacks bundled data files to a directory exposed as ``sys._MEIPASS``.
In development the data lives at the project root (the parent of the ``scada_app``
package). ``resource_path`` returns the correct absolute path in both cases.
"""

from __future__ import annotations

import os
import sys


def resource_path(*parts: str) -> str:
    """Absolute path to a bundled resource given path parts relative to root."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        # <project root> = parent of the scada_app package (this file's dir)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.normpath(os.path.join(base, *parts))
