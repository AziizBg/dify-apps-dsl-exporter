"""Confluence Cloud REST v2 client and storage-format helpers.

Used by the automated tracker sync. Unlike the interactive MCP tools, this talks
to the Confluence REST API directly with an API token, so it can run unattended
(GitHub Actions, cron, etc.).

Required environment variables:
    CONFLUENCE_BASE_URL   e.g. https://1dev.atlassian.net/wiki
    CONFLUENCE_EMAIL      Atlassian account email that owns the API token
    CONFLUENCE_API_TOKEN  API token from https://id.atlassian.com/manage-profile/security/api-tokens
    CONFLUENCE_PAGE_ID    Numeric id of the tracker page to keep in sync
"""

import base64
import html
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()

CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "").rstrip("/")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID")

# Status lozenge colours (Confluence storage uses capitalised colour names).
COLOUR_GREEN = "Green"
COLOUR_YELLOW = "Yellow"
COLOUR_RED = "Red"
COLOUR_GREY = "Grey"


def _require_config() -> None:
    missing = [
        name
        for name, value in (
            ("CONFLUENCE_BASE_URL", CONFLUENCE_BASE_URL),
            ("CONFLUENCE_EMAIL", CONFLUENCE_EMAIL),
            ("CONFLUENCE_API_TOKEN", CONFLUENCE_API_TOKEN),
            ("CONFLUENCE_PAGE_ID", CONFLUENCE_PAGE_ID),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Confluence configuration: " + ", ".join(missing) + ". "
            "Set them in .env (local) or as GitHub Actions secrets."
        )


def _auth_header() -> str:
    raw = f"{CONFLUENCE_EMAIL}:{CONFLUENCE_API_TOKEN}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def get_page(client: httpx.Client, page_id: str) -> dict:
    """Fetch a page's storage body and current version number."""
    _require_config()
    url = f"{CONFLUENCE_BASE_URL}/api/v2/pages/{page_id}"
    resp = client.get(
        url,
        params={"body-format": "storage"},
        headers={"Authorization": _auth_header(), "Accept": "application/json"},
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "title": data["title"],
        "version": data["version"]["number"],
        "storage": data["body"]["storage"]["value"],
    }


def update_page(
    client: httpx.Client,
    page_id: str,
    title: str,
    storage_body: str,
    current_version: int,
    message: str,
) -> dict:
    """Replace a page's body, incrementing its version number."""
    _require_config()
    url = f"{CONFLUENCE_BASE_URL}/api/v2/pages/{page_id}"
    payload = {
        "id": str(page_id),
        "status": "current",
        "title": title,
        "body": {"representation": "storage", "value": storage_body},
        "version": {"number": current_version + 1, "message": message},
    }
    resp = client.put(
        url,
        json=payload,
        headers={
            "Authorization": _auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    resp.raise_for_status()
    return resp.json()


def status_macro(title: str, colour: str) -> str:
    """Render a Confluence status lozenge in storage format."""
    return (
        '<ac:structured-macro ac:name="status">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{html.escape(title)}</ac:parameter>'
        "</ac:structured-macro>"
    )


def info_panel(text_html: str) -> str:
    """Render an info panel in storage format."""
    return (
        '<ac:structured-macro ac:name="info"><ac:rich-text-body>'
        f"<p>{text_html}</p>"
        "</ac:rich-text-body></ac:structured-macro>"
    )


def flag_row_removed(row_html: str) -> str:
    """Replace the first cell of a row with a red 'Removed from Dify' lozenge."""
    replacement = f"<td><p>{status_macro('Removed from Dify', COLOUR_RED)}</p></td>"
    return re.sub(r"<td>.*?</td>", replacement, row_html, count=1, flags=re.DOTALL)
