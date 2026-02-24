#!/usr/bin/env python3
"""Custom login script that uses system Chrome (workaround for Playwright Chromium crash on macOS).

Usage:
    uv run python scripts/login.py
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    # Default storage paths (same as notebooklm-py)
    home = Path.home() / ".notebooklm"
    storage_path = home / "storage_state.json"
    browser_profile = home / "browser_profile"

    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    browser_profile.mkdir(parents=True, exist_ok=True, mode=0o700)

    print("Opening system Chrome for Google login...")
    print(f"Storage: {storage_path}")
    print(f"Profile: {browser_profile}")

    with sync_playwright() as p:
        # Use system Chrome instead of Playwright's bundled Chromium
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(browser_profile),
            headless=False,
            channel="chrome",  # <-- Key difference: use system Chrome
            args=[
                "--disable-blink-features=AutomationControlled",
                "--password-store=basic",
            ],
            ignore_default_args=["--enable-automation"],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://notebooklm.google.com/")

        print("\n=== Instructions ===")
        print("1. Complete the Google login in the browser window")
        print("2. Wait until you see the NotebookLM homepage")
        print("3. Press ENTER here to save and close\n")

        input("[Press ENTER when logged in] ")

        current_url = page.url
        if "notebooklm.google.com" not in current_url:
            print(f"Warning: Current URL is {current_url}")
            resp = input("Save authentication anyway? (y/n) ")
            if resp.lower() != "y":
                context.close()
                sys.exit(1)

        context.storage_state(path=str(storage_path))
        storage_path.chmod(0o600)
        context.close()

    print(f"\nAuthentication saved to: {storage_path}")
    print("You can now use the NotebookLM MCP server!")


if __name__ == "__main__":
    main()
