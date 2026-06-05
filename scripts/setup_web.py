#!/usr/bin/env python3
"""Web-based setup wizard for gsc-gpc-mcp. Run with: python scripts/setup_web.py"""

import json
import os
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent.parent
CREDENTIALS_DIR = ROOT / "credentials"
TEMPLATES_DIR = Path(__file__).parent / "templates"
PORT = 7777

jinja = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)


# ── Domain logic ──────────────────────────────────────────────────────────────


def validate_key_file(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    required = {"type", "project_id", "client_email", "private_key"}
    if not required.issubset(data.keys()) or data.get("type") != "service_account":
        return None
    return data


def key_status(label: str, default_file: str, env_var: str) -> dict:
    filename = os.environ.get(env_var, default_file)
    path = CREDENTIALS_DIR / filename
    data = validate_key_file(path) if path.exists() else None
    return {"label": label, "file": filename, "ok": data is not None, "data": data}


def get_status() -> dict:
    deps_ok = True
    try:
        import fastmcp  # noqa: F401
        import googleapiclient  # noqa: F401
    except ImportError:
        deps_ok = False

    gsc = key_status("Google Search Console", "gsc-service-account.json", "GSC_KEY_FILE")
    gpc = key_status("Google Play Console", "gpc-service-account.json", "GPC_KEY_FILE")

    return {
        "deps_ok": deps_ok,
        "gsc": gsc,
        "gpc": gpc,
        "all_ok": deps_ok and gsc["ok"] and gpc["ok"],
        "env_exists": (ROOT / ".env").exists(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "gpc_package": os.environ.get("GPC_PACKAGE_NAME", ""),
    }


def install_deps() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def create_env(gsc_file: str, gpc_file: str) -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        return
    env_file.write_text(
        f"GSC_KEY_FILE={gsc_file}\n"
        f"GPC_KEY_FILE={gpc_file}\n"
        f"\n"
        f"# Optional: single key for both servers\n"
        f"# GOOGLE_KEY_FILE=google-service-account.json\n"
    )


def save_uploaded_key(target_name: str, file_data: bytes) -> tuple[bool, str]:
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    dest = CREDENTIALS_DIR / target_name
    dest.write_bytes(file_data)
    data = validate_key_file(dest)
    if data:
        return (
            True,
            f"✓ Key uploaded: {target_name} (project: {data['project_id']}, email: {data['client_email']})",
        )
    dest.unlink(missing_ok=True)
    return False, "✗ Invalid service account JSON — file removed."


def parse_multipart(body: bytes, content_type: str) -> dict[str, bytes | str]:
    """Parse multipart/form-data, return dict of field_name → value."""
    boundary = content_type.split("boundary=")[-1].encode()
    parts = body.split(b"--" + boundary)
    fields: dict[str, bytes | str] = {}
    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        header, _, payload = part.partition(b"\r\n\r\n")
        payload = payload.rsplit(b"\r\n", 1)[0]
        header_str = header.decode(errors="replace")
        if 'filename="' in header_str:
            # file field — keep as bytes
            name = header_str.split('name="')[1].split('"')[0]
            fields[name] = payload
        else:
            # text field
            name = header_str.split('name="')[1].split('"')[0]
            fields[name] = payload.decode().strip()
    return fields


def test_gsc_connection() -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(ROOT))
        from shared.auth import build_gsc_service

        svc = build_gsc_service()
        result = svc.sites().list().execute()
        sites = [e["siteUrl"] for e in result.get("siteEntry", [])]
        if sites:
            return True, "Connected. Properties: " + ", ".join(sites)
        return (
            True,
            "Connected — no properties accessible yet (add service account email in Search Console)",
        )
    except Exception as e:
        return False, f"Failed: {e}"


def test_gpc_connection(package_name: str) -> tuple[bool, str]:
    if not package_name:
        return False, "Package name required (e.g. com.example.app)"
    try:
        sys.path.insert(0, str(ROOT))
        from shared.auth import build_gpc_service

        svc = build_gpc_service()
        result = svc.reviews().list(packageName=package_name, maxResults=5).execute()
        count = len(result.get("reviews", []))
        return True, f"Connected — {count} review(s) returned for {package_name}"
    except Exception as e:
        return False, f"Failed: {e}"


# ── HTTP handler ──────────────────────────────────────────────────────────────


class Handler(BaseHTTPRequestHandler):
    _message: str = ""
    _message_ok: bool = True

    def log_message(self, *args):
        pass

    def render(self, message: str = "", message_ok: bool = True, code: int = 200) -> None:
        ctx = get_status()
        ctx["message"] = message
        ctx["message_ok"] = message_ok
        body = jinja.get_template("setup.html").render(**ctx).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, path: str, msg: str = "", ok: bool = True) -> None:
        Handler._message = msg
        Handler._message_ok = ok
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/stop":
            self.render("Wizard stopped. You can close this tab.")
            os._exit(0)
        if path == "/test/gsc":
            success, msg = test_gsc_connection()
            self.redirect("/", msg, success)
            return
        msg = Handler._message
        msg_ok = Handler._message_ok
        Handler._message = ""
        Handler._message_ok = True
        self.render(msg, msg_ok)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        path = urlparse(self.path).path
        content_type = self.headers.get("Content-Type", "")

        if path == "/install":
            success = install_deps()
            self.redirect(
                "/",
                "Dependencies installed." if success else "Installation failed — check terminal.",
                success,
            )

        elif path == "/create-env":
            s = get_status()
            create_env(s["gsc"]["file"], s["gpc"]["file"])
            self.redirect("/", ".env file created.")

        elif path == "/upload":
            fields = parse_multipart(body, content_type)
            target = fields.get("target", "")
            file_data = fields.get("file", b"")
            if target and file_data:
                success, msg = save_uploaded_key(str(target), bytes(file_data))
            else:
                success, msg = False, "Upload failed — no file received."
            self.redirect("/", msg, success)

        elif path == "/test/gpc":
            fields = parse_multipart(body, content_type)
            package_name = str(fields.get("package_name", "")).strip()
            if not package_name:
                # fall back to env
                package_name = os.environ.get("GPC_PACKAGE_NAME", "")
            success, msg = test_gpc_connection(package_name)
            self.redirect("/", msg, success)

        else:
            self.redirect("/")


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    server = HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"\n  Setup wizard → {url}")
    print("  Ctrl+C to stop\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")


if __name__ == "__main__":
    main()
