"""A small loopback-only UI for the local library pipeline."""
from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from game_emulator.library import import_library, list_games

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GAME: Emulator</title><style>
body{font:16px system-ui;max-width:960px;margin:2rem auto;padding:0 1rem;background:#111827;color:#f3f4f6}
input,button{font:inherit;padding:.7rem;border-radius:.5rem;border:1px solid #64748b;width:100%;box-sizing:border-box;margin:.25rem 0 1rem}
button{background:#7c3aed;color:white;border:0;font-weight:700}small{color:#cbd5e1}.panel{background:#1f2937;padding:1rem;border-radius:.8rem;margin:1rem 0}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:.5rem;border-bottom:1px solid #475569;overflow-wrap:anywhere}
</style><h1>GAME: Emulator</h1><p>Local library intake · files stay on this device · originals are never modified.</p>
<div class="panel"><h2>Import a folder</h2><form method="post" action="/import">
<label>Source folder path<input name="source" required placeholder="/path/to/your/game-files"></label>
<label>Library folder path<input name="library" required value="__DEFAULT_LIBRARY__"></label>
<label>Rights basis for this batch<input name="rights_basis" required placeholder="e.g. personal dumps / homebrew / files licensed for use"></label>
<label>Source label<input name="source_label" value="user-selected local folder"></label>
<button type="submit">Import, hash, classify & deduplicate</button></form>
<small>Choose folders on the computer running this app. The page cannot browse your phone or another computer's files by itself. No downloads, archive extraction, or game execution occurs.</small></div>
<div class="panel"><h2>Library</h2><p>__STATUS__</p><table><thead><tr><th>System</th><th>File</th><th>Size</th><th>SHA-256</th></tr></thead><tbody>__ROWS__</tbody></table></div></html>"""


def create_handler(default_library: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            return

        def send_html(self, body: str, status: int = 200):
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path not in ("/", "/index.html"):
                self.send_html("Not found", 404)
                return
            params = parse_qs(self.path.partition("?")[2])
            library = Path(params.get("library", [str(default_library)])[0]).expanduser()
            games = list_games(library)
            rows = "".join(
                "<tr><td>{}</td><td>{}</td><td>{:,} B</td><td><code>{}</code></td></tr>".format(
                    html.escape(str(g["system"])), html.escape(str(g["filename"])),
                    int(g["size_bytes"]), html.escape(str(g["sha256"]))
                ) for g in games
            ) or '<tr><td colspan="4">No files imported yet.</td></tr>'
            body = PAGE.replace("__DEFAULT_LIBRARY__", html.escape(str(default_library), quote=True))
            body = body.replace("__STATUS__", f"{len(games)} cataloged files in {html.escape(str(library))}")
            self.send_html(body.replace("__ROWS__", rows))

        def do_POST(self):
            allowed_hosts = {
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
                f"[::1]:{self.server.server_port}",
            }
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if host not in allowed_hosts or (origin and origin not in {f"http://{host}", f"https://{host}"}):
                self.send_html("Forbidden origin/host", 403)
                return
            if self.path != "/import":
                self.send_html("Not found", 404)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 16_384:
                self.send_html("Invalid form size", 400)
                return
            values = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
            def get(key: str) -> str:
                return values.get(key, [""])[0].strip()
            try:
                summary = import_library(
                    Path(get("source")), Path(get("library") or str(default_library)),
                    rights_basis=get("rights_basis"), source_label=get("source_label") or "local import",
                )
                detail = html.escape(json.dumps(summary, indent=2))
                self.send_html("<h1>Import finished</h1><pre>" + detail +
                               '</pre><p><a href="/">Return to library</a></p>')
            except (OSError, ValueError) as exc:
                self.send_html("<h1>Import blocked</h1><pre>" + html.escape(str(exc)) +
                               '</pre><p><a href="/">Return</a></p>', 400)
    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local GAME: Emulator library dashboard")
    parser.add_argument("--library", type=Path, default=Path.home() / "GAME-Emulator-Library")
    parser.add_argument("--host", default="127.0.0.1", help="must remain loopback-only")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "::1", "localhost"):
        parser.error("security: dashboard must bind to loopback only")
    server = HTTPServer((args.host, args.port), create_handler(args.library.expanduser().resolve()))
    print(f"GAME: Emulator dashboard: http://127.0.0.1:{args.port}")
    print("Keep this service local; it does not expose the library to your network.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
