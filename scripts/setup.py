#!/usr/bin/env python3
"""Initial setup wizard for gsc-gpc-mcp."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CREDENTIALS_DIR = ROOT / "credentials"

# ── ANSI colours ──────────────────────────────────────────────────────────────
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def err(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {CYAN}→{RESET} {msg}")


def header(title: str) -> None:
    print(f"\n{BOLD}{title}{RESET}")
    print("─" * len(title))


def pause(prompt: str = "Press Enter to continue...") -> str:
    return input(f"\n  {CYAN}{prompt}{RESET} ").strip()


# ── Checks ────────────────────────────────────────────────────────────────────


def check_python() -> bool:
    v = sys.version_info
    if v >= (3, 11):
        ok(f"Python {v.major}.{v.minor}.{v.micro}")
        return True
    err(f"Python {v.major}.{v.minor} found — 3.11+ required")
    return False


def check_docker() -> bool:
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True, timeout=5)
        ok("Docker available")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        warn("Docker not found — needed for containerised deployment, optional for local dev")
        return False


def check_deps() -> bool:
    try:
        import fastmcp  # noqa: F401
        import googleapiclient  # noqa: F401

        ok("Dependencies installed (fastmcp, google-api-python-client)")
        return True
    except ImportError:
        warn("Dependencies not installed")
        return False


def install_deps() -> bool:
    print()
    info("Running: pip install -e .")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        ok("Dependencies installed successfully")
        return True
    err("Installation failed:")
    print(result.stderr[-500:])
    return False


def validate_key_file(path: Path) -> dict | None:
    """Return parsed JSON if valid service account key, else None."""
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    required = {"type", "project_id", "client_email", "private_key"}
    if not required.issubset(data.keys()):
        return None
    if data.get("type") != "service_account":
        return None
    return data


def check_key(name: str, default_filename: str, env_var: str) -> tuple[bool, dict | None]:
    filename = os.environ.get(env_var, default_filename)
    path = CREDENTIALS_DIR / filename
    if not path.exists():
        err(f"{name} key not found: credentials/{filename}")
        return False, None
    data = validate_key_file(path)
    if data is None:
        err(f"{name} key is not a valid service account JSON: {filename}")
        return False, None
    ok(f"{name} key valid  (project: {data['project_id']}, email: {data['client_email']})")
    return True, data


# ── Steps ─────────────────────────────────────────────────────────────────────


def step_prerequisites() -> bool:
    header("Step 1 — Prerequisites")
    py_ok = check_python()
    check_docker()
    if not py_ok:
        return False
    if not check_deps():
        answer = pause("Install dependencies now? [Y/n]")
        if answer.lower() not in ("n", "no"):
            if not install_deps():
                return False
    return True


def step_credentials() -> bool:
    header("Step 2 — Service Account Keys")

    CREDENTIALS_DIR.mkdir(exist_ok=True)

    gsc_ok, gsc_data = check_key("GSC", "gsc-service-account.json", "GSC_KEY_FILE")
    gpc_ok, gpc_data = check_key("GPC", "gpc-service-account.json", "GPC_KEY_FILE")

    if not gsc_ok or not gpc_ok:
        print()
        info("To create service accounts, follow these steps:\n")
        print(
            "  1. Open https://console.cloud.google.com/iam-admin/serviceaccounts\n"
            "  2. Enable APIs:\n"
            "       • Google Search Console API  (for GSC)\n"
            "       • Google Play Android Developer API  (for GPC)\n"
            "  3. Create service accounts and download JSON keys\n"
            "  4. Place files in credentials/:\n"
            "       credentials/gsc-service-account.json\n"
            "       credentials/gpc-service-account.json\n"
            "  5. Grant access:\n"
            "       GSC → Search Console → Settings → Users → add service account email\n"
            "       GPC → Play Console → Setup → API access → grant service account\n"
        )
        answer = pause("Keys placed? Re-check now? [Y/n]")
        if answer.lower() not in ("n", "no"):
            gsc_ok, gsc_data = check_key("GSC", "gsc-service-account.json", "GSC_KEY_FILE")
            gpc_ok, gpc_data = check_key("GPC", "gpc-service-account.json", "GPC_KEY_FILE")

    if not gsc_ok and not gpc_ok:
        warn("No keys found — you can re-run setup later: python scripts/setup.py")
        return False

    return True


def step_env() -> None:
    header("Step 3 — Environment")

    env_file = ROOT / ".env"
    if env_file.exists():
        ok(".env already exists — skipping")
        return

    gsc_key = os.environ.get("GSC_KEY_FILE", "gsc-service-account.json")
    gpc_key = os.environ.get("GPC_KEY_FILE", "gpc-service-account.json")

    content = (
        f"# gsc-gpc-mcp environment\n"
        f"GSC_KEY_FILE={gsc_key}\n"
        f"GPC_KEY_FILE={gpc_key}\n"
        f"\n"
        f"# Ports (only needed for local HTTP mode, not Docker)\n"
        f"# GSC_PORT=8001\n"
        f"# GPC_PORT=8002\n"
        f"\n"
        f"# Optional: one key for both servers\n"
        f"# GOOGLE_KEY_FILE=google-service-account.json\n"
    )
    env_file.write_text(content)
    ok(f".env created: {env_file}")


def test_gsc_connection() -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(ROOT))
        from shared.auth import build_gsc_service

        svc = build_gsc_service()
        result = svc.sites().list().execute()
        sites = [e["siteUrl"] for e in result.get("siteEntry", [])]
        if sites:
            return True, "Properties: " + ", ".join(sites)
        return (
            True,
            "Connected — no properties accessible yet (add service account in Search Console)",
        )
    except Exception as e:
        return False, str(e)


def test_gpc_connection(package_name: str) -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(ROOT))
        from shared.auth import build_gpc_service

        svc = build_gpc_service()
        result = svc.reviews().list(packageName=package_name, maxResults=5).execute()
        count = len(result.get("reviews", []))
        return True, f"Connected — {count} review(s) returned for {package_name}"
    except Exception as e:
        return False, str(e)


def step_test_connections(gsc_ok: bool, gpc_ok: bool) -> None:
    header("Step 3 — Test Connections")

    answer = pause("Test API connections now? [Y/n]")
    if answer.lower() in ("n", "no"):
        info("Skipped — test later by re-running setup")
        return

    if gsc_ok:
        info("Testing GSC...")
        success, msg = test_gsc_connection()
        if success:
            ok(f"GSC: {msg}")
        else:
            err(f"GSC: {msg}")
    else:
        warn("GSC: skipped (no key)")

    if gpc_ok:
        package = os.environ.get("GPC_PACKAGE_NAME", "").strip()
        if not package:
            package = pause("GPC package name (e.g. com.example.app):").strip()
        if package:
            info(f"Testing GPC with {package}...")
            success, msg = test_gpc_connection(package)
            if success:
                ok(f"GPC: {msg}")
            else:
                err(f"GPC: {msg}")
        else:
            warn("GPC: skipped (no package name)")
    else:
        warn("GPC: skipped (no key)")


def step_run_tests() -> None:
    header("Step 4 — Unit Tests")

    answer = pause("Run unit tests now? [Y/n]")
    if answer.lower() in ("n", "no"):
        info("Skipped — run later with: make test")
        return

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=short", "-q"],
        cwd=ROOT,
    )
    if result.returncode == 0:
        ok("All tests passed")
    else:
        warn("Some tests failed — check output above")


def step_summary(creds_ok: bool) -> None:
    header("Setup Summary")

    if creds_ok:
        ok("Ready to run")
        print()
        print(f"  {BOLD}Local (stdio):{RESET}")
        print("    python -m gsc.server")
        print("    python -m gpc.server\n")
        print(f"  {BOLD}Local (HTTP):{RESET}")
        print("    PORT=8001 python -m gsc.server")
        print("    PORT=8002 python -m gpc.server\n")
        print(f"  {BOLD}Docker:{RESET}")
        print("    docker compose up -d\n")
        print(f"  {BOLD}Register in authmcp-gateway:{RESET}")
        print("    See README.md → Setup → Step 4")
    else:
        warn("Setup incomplete — add credentials and re-run: python scripts/setup.py")

    print()


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    print(f"\n{BOLD}{CYAN}gsc-gpc-mcp — Setup Wizard{RESET}")
    print("=" * 40)

    if not step_prerequisites():
        sys.exit(1)

    creds_ok = step_credentials()
    gsc_ok, _ = check_key("GSC", "gsc-service-account.json", "GSC_KEY_FILE")
    gpc_ok, _ = check_key("GPC", "gpc-service-account.json", "GPC_KEY_FILE")
    step_test_connections(gsc_ok, gpc_ok)
    step_env()
    step_run_tests()
    step_summary(creds_ok)


if __name__ == "__main__":
    main()
