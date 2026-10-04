"""Capture the control-related REST tree of an Eaton Network-M2/M3 card.

Read-only: only GET requests are made (plus the OAuth2 login and the session
logout). The walk follows ``@id`` links below the chosen roots and records every
action link it sees (keys starting with ``#``) without calling it.

Usage:
    EATON_PASSWORD=... python scripts/capture_rest_tree.py \
        --host ups.local --username hass --output docs/control-api/rest_tree_m3.json

The card allows one session per account, so use an account that is not logged
in to the web UI. Use --cafile with the card's web certificate, or --insecure
for the card's self-signed certificate on a trusted network.

Output: JSON with ``version``, ``resources`` ({path: body}), ``actions``
({action_path: advertised_by}) and ``errors`` ({path: message}).
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

DEFAULT_ROOTS = [
    "protectionService",
    "powerService",
    "scheduleService",
    "powerDistributions/1",
    "powerDistributions/1/settings",
    "powerDistributions/1/outlets",
    "powerDistributions/1/backupSystem/powerBank/settings",
    "managers/1/actions",
]


class Card:
    def __init__(self, host: str, context: ssl.SSLContext) -> None:
        self.base = f"https://{host}"
        self.context = context
        self.token = ""
        self.session = ""

    def request(
        self, method: str, path: str, body: dict | None = None
    ) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(  # noqa: S310 - base is always https://
            self.base + path, data=data, method=method
        )
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(  # noqa: S310
                req, context=self.context, timeout=20
            ) as r:
                raw = r.read()
                status = r.status
        except urllib.error.HTTPError as err:
            raw = err.read()
            status = err.code
        try:
            return status, json.loads(raw) if raw else None
        except ValueError:
            return status, raw.decode(errors="replace")

    def login(self, version: str, username: str, password: str) -> None:
        status, answer = self.request(
            "POST",
            f"/rest/mbdetnrs/{version}/oauth2/token/",
            {
                "username": username,
                "password": password,
                "grant_type": "password",
                "scope": "GUIAccess",
            },
        )
        if status != 200 or not isinstance(answer, dict):
            msg = f"login failed ({status}): {answer}"
            raise RuntimeError(msg)
        self.token = answer["access_token"]
        self.session = answer.get("session", "")

    def logout(self) -> None:
        if not self.session:
            return
        path = self.session
        if not path.startswith("/rest/"):
            path = "/rest" + path
        status, answer = self.request("DELETE", path)
        if not 200 <= status < 300:
            print(f"warning: logout returned {status}: {answer}", file=sys.stderr)


def walk_links(value: Any, links: list[str], actions: dict[str, str], here: str):
    """Collect @id links and #action links found anywhere in a body."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "@id" and isinstance(item, str):
                links.append(item)
            elif key.startswith("#") and isinstance(item, str):
                actions[item] = here
            else:
                walk_links(item, links, actions, here)
    elif isinstance(value, list):
        for item in value:
            walk_links(item, links, actions, here)


def normalise(link: str, prefix: str) -> str:
    """Turn '/mbdetnrs/2.0/x', 'mbdetnrs/2.0/x' or '/rest/...' into '/rest/...'."""
    link = link.split("?", 1)[0].rstrip("/")
    if link.startswith("/rest/"):
        return link
    return (
        "/rest/" + link.lstrip("/")
        if link.lstrip("/").startswith("mbdetnrs/")
        else prefix + "/" + link.lstrip("/")
    )


def crawl(
    card: Card, version: str, extra_roots: list[str] | None, limit: int
) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    """Breadth-first GET of every @id below the roots."""
    prefix = f"/rest/mbdetnrs/{version}"
    roots = [f"{prefix}/{r.strip('/')}" for r in (extra_roots or DEFAULT_ROOTS)]
    resources: dict[str, Any] = {}
    actions: dict[str, str] = {}
    errors: dict[str, str] = {}
    queue = deque(roots)
    try:
        while queue and len(resources) + len(errors) < limit:
            path = queue.popleft()
            if path in resources or path in errors or "/actions/" in path:
                continue
            status, body = card.request("GET", path + "?$expand=1")
            if status != 200:
                errors[path] = f"{status}: {body}"
                continue
            resources[path] = body
            print(f"GET {path}")
            links: list[str] = []
            walk_links(body, links, actions, path)
            for link in links:
                target = normalise(link, prefix)
                if any(target.startswith(root) for root in roots):
                    queue.append(target)
    finally:
        card.logout()

    return resources, actions, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument(
        "--password", default=os.environ.get("EATON_PASSWORD"), help="or EATON_PASSWORD"
    )
    parser.add_argument(
        "--version",
        choices=["auto", "1.0", "2.0"],
        default="auto",
        help="REST version (M2 = 1.0, M3 = 2.0); auto tries 2.0 then 1.0",
    )
    parser.add_argument("--root", action="append", help="extra/override roots")
    parser.add_argument("--max-resources", type=int, default=400)
    parser.add_argument("--cafile")
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not args.password:
        parser.error("--password or EATON_PASSWORD is required")

    context = ssl.create_default_context(cafile=args.cafile)
    if args.insecure:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    card = Card(args.host, context)
    versions = ["2.0", "1.0"] if args.version == "auto" else [args.version]
    version = ""
    for candidate in versions:
        try:
            card.login(candidate, args.username, args.password)
            version = candidate
            break
        except RuntimeError as err:
            print(f"{candidate}: {err}", file=sys.stderr)
    if not version:
        return 1

    resources, actions, errors = crawl(card, version, args.root, args.max_resources)

    Path(args.output).write_text(
        json.dumps(
            {
                "host": args.host,
                "version": version,
                "resources": resources,
                "actions": dict(sorted(actions.items())),
                "errors": errors,
            },
            indent=2,
            sort_keys=False,
        )
        + "\n"
    )
    print(
        f"wrote {args.output}: {len(resources)} resources, "
        f"{len(actions)} actions, {len(errors)} errors"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
