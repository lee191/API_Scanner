#!/usr/bin/env python3
"""GUI launcher entry point."""

from __future__ import annotations

from typing import Optional

from route_api_discovery import gui_main


def main(initial_url: Optional[str] = None, initial_output: Optional[str] = None) -> int:
    return gui_main(initial_url=initial_url, initial_output=initial_output)
