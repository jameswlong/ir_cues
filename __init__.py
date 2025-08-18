#ir_cues/__init__.py

"""
ir-cues: Incident Response cues at your fingertips.
Quick command recipes for DFIR tasks (Windows, Linux, Cloud, Browser).
"""

__version__ = "0.1.0"

# Optionally, make the main CLI app importable
from .cli import app

__all__ = ["app", "__version__"]