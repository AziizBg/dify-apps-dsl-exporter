"""Delete every workflow marked "Delete" in the Confluence tracker, then notify Slack.

Reads the tracker page, finds rows whose Decision column is "Delete" and that still
exist in Dify, deletes them from Dify, and posts a Slack message listing what was
removed. Deletion is destructive, so it is gated behind an explicit --yes flag (or
CONFIRM_PRUNE=DELETE_MARKED). Without it, the script only lists the candidates.

After pruning, run `./run.sh sync` so the page flags the removed rows in red and the
status/Slack counts refresh.

Usage:
    python src/prune_deleted.py            # list candidates only (safe)
    python src/prune_deleted.py --yes      # actually delete + notify Slack
    python src/prune_deleted.py --yes --no-slack
"""

import argparse
import asyncio
import os
from datetime import datetime, timezone

import httpx

import confluence
import dify_api
import slack_notify
import sync_tracker

DELETE_DECISION = "delete"


def find_delete_marked(storage: str, dify_ids: set[str]) -> list[dict]:
    """Return tracker rows marked 'Delete' that still exist in Dify."""
    _, rows = sync_tracker.parse_existing_rows(storage)
    return [
        r
        for r in rows
        if r.get("decision", "").strip().lower() == DELETE_DECISION and r["app_id"] in dify_ids
    ]


async def _delete_targets(targets: list[dict]) -> tuple[list[dict], list[dict]]:
    """Delete each target from Dify and verify removal."""
    async with httpx.AsyncClient(timeout=60) as client:
        access_token = await dify_api.login_and_get_token(client)
        for row in targets:
            await dify_api.delete_app(
                access_token, {"id": row["app_id"], "name": row["name"]}, client
            )
        remaining_apps, _ = await dify_api.get_app_list(access_token, client)
    remaining_ids = {a["id"] for a in remaining_apps}
    deleted = [r for r in targets if r["app_id"] not in remaining_ids]
    failed = [r for r in targets if r["app_id"] in remaining_ids]
    return deleted, failed


def run(confirm: bool = False, notify: bool = True) -> dict:
    print("Fetching apps from Dify...")
    dify_apps = asyncio.run(sync_tracker.fetch_dify_apps())
    dify_ids = {a["id"] for a in dify_apps if a.get("id")}
    print(f"  {len(dify_ids)} apps found.")

    page_id = confluence.CONFLUENCE_PAGE_ID
    page_url = f"{confluence.CONFLUENCE_BASE_URL}/pages/{page_id}"
    with httpx.Client(timeout=60) as client:
        print("Reading Confluence page...")
        page = confluence.get_page(client, page_id)
    targets = find_delete_marked(page["storage"], dify_ids)

    print(f"Workflows marked 'Delete' and still live in Dify: {len(targets)}")
    for row in targets:
        print(f"  - {row['name']} ({row['app_id']})")

    if not targets:
        print("Nothing to delete.")
        return {"deleted": [], "failed": []}

    if not confirm:
        print(
            "\nDry run: no workflows deleted. Re-run with --yes (or CONFIRM_PRUNE=DELETE_MARKED) "
            "to actually delete the workflows above."
        )
        return {"candidates": targets}

    print(f"\nDeleting {len(targets)} workflow(s) from Dify...")
    deleted, failed = asyncio.run(_delete_targets(targets))
    print(f"  Deleted: {len(deleted)}, Failed: {len(failed)}")

    # Flag the deleted rows on the tracker ("Removed from Dify") by re-syncing
    # against the now-shorter Dify app list.
    print("Updating Confluence to flag deleted workflows...")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    remaining_apps = asyncio.run(sync_tracker.fetch_dify_apps())
    with httpx.Client(timeout=60) as client:
        sync_tracker.update_confluence(
            client,
            remaining_apps,
            today,
            version_message=f"Flag {len(deleted)} workflow(s) deleted via prune ({today})",
        )

    if notify:
        print("Posting deletion notice to Slack...")
        messages = slack_notify.build_deletion_messages(deleted, failed, page_url)
        slack_notify.post_all(messages)
        print(f"  Slack: {len(messages)} message(s) sent.")

    return {"deleted": deleted, "failed": failed}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete workflows marked 'Delete' in the Confluence tracker."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually delete (otherwise lists candidates only).",
    )
    parser.add_argument(
        "--no-slack", action="store_true", help="Delete but skip the Slack notification."
    )
    args = parser.parse_args()
    confirm = args.yes or os.getenv("CONFIRM_PRUNE", "") == "DELETE_MARKED"
    run(confirm=confirm, notify=not args.no_slack)


if __name__ == "__main__":
    main()
