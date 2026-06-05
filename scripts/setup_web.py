#!/usr/bin/env python3
"""Web-based setup wizard for gsc-gpc-mcp. Opens in browser, no extra deps."""

import json
import os
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
CREDENTIALS_DIR = ROOT / "credentials"
PORT = 7777


# ── Helpers ───────────────────────────────────────────────────────────────────


def validate_key_file(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    required = {"type", "project_id", "client_email", "private_key"}
    if not required.issubset(data.keys()) or data.get("type") != "service_account":
        return None
    return data


def get_status() -> dict:
    deps_ok = True
    try:
        import fastmcp  # noqa: F401
        import googleapiclient  # noqa: F401
    except ImportError:
        deps_ok = False

    gsc_file = os.environ.get("GSC_KEY_FILE", "gsc-service-account.json")
    gpc_file = os.environ.get("GPC_KEY_FILE", "gpc-service-account.json")
    shared_file = os.environ.get("GOOGLE_KEY_FILE", "")

    gsc_path = CREDENTIALS_DIR / gsc_file
    gpc_path = CREDENTIALS_DIR / gpc_file

    gsc_data = validate_key_file(gsc_path) if gsc_path.exists() else None
    gpc_data = validate_key_file(gpc_path) if gpc_path.exists() else None

    env_exists = (ROOT / ".env").exists()

    return {
        "deps_ok": deps_ok,
        "gsc": {"file": gsc_file, "ok": gsc_data is not None, "data": gsc_data},
        "gpc": {"file": gpc_file, "ok": gpc_data is not None, "data": gpc_data},
        "shared_key": shared_file,
        "env_exists": env_exists,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def install_deps() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, result.stdout + result.stderr


def create_env(gsc_file: str, gpc_file: str) -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        return
    env_file.write_text(
        f"GSC_KEY_FILE={gsc_file}\n"
        f"GPC_KEY_FILE={gpc_file}\n"
        f"\n"
        f"# Optional: single key for both\n"
        f"# GOOGLE_KEY_FILE=google-service-account.json\n"
    )


# ── HTML ──────────────────────────────────────────────────────────────────────


def render_badge(ok: bool, label: str) -> str:
    color = "#22c55e" if ok else "#ef4444"
    icon = "✓" if ok else "✗"
    return (
        f'<span style="background:{color};color:#fff;border-radius:4px;'
        f'padding:2px 8px;font-size:13px;font-weight:600">{icon} {label}</span>'
    )


def render_page(status: dict, message: str = "") -> str:
    s = status

    def key_row(name: str, info: dict) -> str:
        badge = render_badge(info["ok"], "valid" if info["ok"] else "missing")
        detail = ""
        if info["ok"] and info["data"]:
            detail = (
                f'<div class="detail">'
                f"project: <b>{info['data']['project_id']}</b> · "
                f"email: <b>{info['data']['client_email']}</b>"
                f"</div>"
            )
        upload = (
            (
                f'<form method="POST" action="/upload" enctype="multipart/form-data" style="margin-top:8px">'
                f'<input type="hidden" name="target" value="{info["file"]}">'
                f'<input type="file" name="file" accept=".json" required style="font-size:13px">'
                f'<button type="submit" class="btn-sm">Upload</button>'
                f"</form>"
            )
            if not info["ok"]
            else ""
        )
        return (
            f'<div class="card">'
            f'<div class="card-title">{name} {badge}</div>'
            f'<div class="detail">File: <code>credentials/{info["file"]}</code></div>'
            f"{detail}{upload}"
            f"</div>"
        )

    msg_html = f'<div class="msg">{message}</div>' if message else ""

    all_ok = s["deps_ok"] and s["gsc"]["ok"] and s["gpc"]["ok"]
    ready_html = ""
    if all_ok:
        ready_html = """
        <div class="ready">
            <b>✓ Setup complete!</b><br><br>
            <b>Local HTTP mode:</b><br>
            <code>PORT=8001 python -m gsc.server</code><br>
            <code>PORT=8002 python -m gpc.server</code><br><br>
            <b>Docker:</b><br>
            <code>docker compose up -d</code><br><br>
            See <a href="https://github.com/loglux/authmcp-gateway" target="_blank">authmcp-gateway</a>
            for registering backends.
        </div>"""

    install_btn = (
        ""
        if s["deps_ok"]
        else (
            '<form method="POST" action="/install" style="margin-top:8px">'
            '<button type="submit" class="btn">Install dependencies</button>'
            "</form>"
        )
    )

    env_badge = render_badge(s["env_exists"], ".env exists" if s["env_exists"] else ".env missing")
    env_btn = (
        ""
        if s["env_exists"]
        else (
            '<form method="POST" action="/create-env" style="margin-top:8px">'
            '<button type="submit" class="btn-sm">Create .env</button>'
            "</form>"
        )
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>gsc-gpc-mcp Setup</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0 }}
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 32px 16px }}
  .wrap {{ max-width: 680px; margin: 0 auto }}
  h1 {{ font-size: 22px; font-weight: 700; color: #f8fafc; margin-bottom: 4px }}
  .sub {{ color: #94a3b8; font-size: 14px; margin-bottom: 28px }}
  .section {{ margin-bottom: 24px }}
  .section-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: #64748b; margin-bottom: 10px }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px }}
  .card-title {{ font-weight: 600; font-size: 15px; margin-bottom: 6px }}
  .detail {{ color: #94a3b8; font-size: 13px; margin-top: 4px }}
  code {{ background: #0f172a; border: 1px solid #334155; border-radius: 4px; padding: 1px 6px; font-size: 13px; color: #7dd3fc }}
  .btn {{ background: #3b82f6; color: #fff; border: none; padding: 8px 18px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600 }}
  .btn:hover {{ background: #2563eb }}
  .btn-sm {{ background: #334155; color: #e2e8f0; border: none; padding: 5px 12px; border-radius: 5px; cursor: pointer; font-size: 13px; font-weight: 500 }}
  .btn-sm:hover {{ background: #475569 }}
  .msg {{ background: #14532d; border: 1px solid #16a34a; border-radius: 6px; padding: 10px 14px; margin-bottom: 20px; font-size: 14px; color: #86efac }}
  .ready {{ background: #1e3a5f; border: 1px solid #3b82f6; border-radius: 8px; padding: 16px; margin-top: 16px; font-size: 14px; line-height: 1.8 }}
  .ready code {{ display: block; margin: 2px 0 }}
  a {{ color: #60a5fa }}
  .step {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; font-size: 14px; color: #94a3b8 }}
  .step-num {{ background: #334155; color: #94a3b8; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; margin-top: 1px }}
</style>
</head>
<body>
<div class="wrap">
  <h1>gsc-gpc-mcp</h1>
  <div class="sub">Setup Wizard</div>

  {msg_html}

  <div class="section">
    <div class="section-title">Prerequisites</div>
    <div class="card">
      <div class="card-title">Python {render_badge(True, s["python"])}</div>
      <div class="detail">Dependencies {render_badge(s["deps_ok"], "installed" if s["deps_ok"] else "missing")}</div>
      {install_btn}
    </div>
  </div>

  <div class="section">
    <div class="section-title">Service Account Keys</div>
    <div class="card" style="margin-bottom:16px;border-color:#334155">
      <div class="card-title" style="font-size:13px;color:#94a3b8">How to create service accounts</div>
      <div class="step"><div class="step-num">1</div><div>Open <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank">Google Cloud Console → Service Accounts</a></div></div>
      <div class="step"><div class="step-num">2</div><div>Enable <b>Google Search Console API</b> and <b>Google Play Android Developer API</b></div></div>
      <div class="step"><div class="step-num">3</div><div>Create two service accounts, download JSON keys, upload below</div></div>
      <div class="step"><div class="step-num">4</div><div>GSC: Search Console → Settings → Users → add service account email</div></div>
      <div class="step"><div class="step-num">5</div><div>GPC: Play Console → Setup → API access → grant service account</div></div>
    </div>
    {key_row("Google Search Console", s["gsc"])}
    {key_row("Google Play Console", s["gpc"])}
  </div>

  <div class="section">
    <div class="section-title">Environment</div>
    <div class="card">
      <div class="card-title">.env file {env_badge}</div>
      <div class="detail">Stores key file names for local and Docker usage</div>
      {env_btn}
    </div>
  </div>

  {ready_html}

  <div style="margin-top:32px;font-size:12px;color:#334155;text-align:center">
    Refresh to recheck status · <a href="/stop">Stop wizard</a>
  </div>
</div>
</body>
</html>"""


# ── HTTP handler ──────────────────────────────────────────────────────────────


class Handler(BaseHTTPRequestHandler):
    message = ""

    def log_message(self, *args):
        pass  # silence default access log

    def send_html(self, html: str, code: int = 200) -> None:
        body = html.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, path: str, msg: str = "") -> None:
        Handler.message = msg
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/stop":
            self.send_html("<p>Wizard stopped. You can close this tab.</p>")
            os._exit(0)
        status = get_status()
        msg = Handler.message
        Handler.message = ""
        self.send_html(render_page(status, msg))

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if path == "/install":
            ok_flag, _ = install_deps()
            self.redirect(
                "/",
                "Dependencies installed successfully."
                if ok_flag
                else "Installation failed — check terminal.",
            )

        elif path == "/create-env":
            s = get_status()
            create_env(s["gsc"]["file"], s["gpc"]["file"])
            self.redirect("/", ".env file created.")

        elif path == "/upload":
            # Minimal multipart parser — no extra deps
            content_type = self.headers.get("Content-Type", "")
            boundary = content_type.split("boundary=")[-1].encode()
            parts = body.split(b"--" + boundary)
            target_name = ""
            file_data = b""
            for part in parts:
                if b'name="target"' in part:
                    target_name = part.split(b"\r\n\r\n", 1)[-1].strip().decode()
                elif b'name="file"' in part and b"filename=" in part:
                    file_data = part.split(b"\r\n\r\n", 1)[-1].rsplit(b"\r\n", 1)[0]

            if target_name and file_data:
                dest = CREDENTIALS_DIR / target_name
                CREDENTIALS_DIR.mkdir(exist_ok=True)
                dest.write_bytes(file_data)
                data = validate_key_file(dest)
                if data:
                    self.redirect("/", f"Key uploaded and validated: {target_name}")
                else:
                    dest.unlink(missing_ok=True)
                    self.redirect("/", "Invalid service account JSON — file removed.")
            else:
                self.redirect("/", "Upload failed — no file received.")
        else:
            self.redirect("/")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    server = HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"\n  Setup wizard running at {url}")
    print("  Press Ctrl+C to stop\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Wizard stopped.")


if __name__ == "__main__":
    main()
