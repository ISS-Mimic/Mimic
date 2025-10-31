#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISS Mimic setup: Bullseye, Bookworm, Trixie
- Safe path handling (no renames), robust sudo/root behavior
- Noninteractive apt, lock/repair handling, lean deps (no *-dev)
- Locale setup without forcing LC_ALL systemwide
- Kivy runtime libs + optional pip Kivy
- Headless priming of data products
"""

import os
import sys
import time
import shlex
import argparse
import shutil
import subprocess
import stat
from pathlib import Path
from getpass import getuser

try:
    import pwd
except ImportError:
    pwd = None

# ───────────────────────── Colors ─────────────────────────
RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
BLUE = '\033[94m'; CYAN = '\033[96m'; RESET = '\033[0m'

# ───────────────────── Repo / Paths ──────────────────────
REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)

HOME = Path.home()
SRC_INITIAL = REPO_ROOT / 'Pi' / 'InitialFiles'
DEST_DATA = HOME / '.mimic_data'
DEST_DATA.mkdir(parents=True, exist_ok=True)

# Log file (tee console output here too)
LOG_PATH = DEST_DATA / 'install.log'

# ─────────────── Apt non-interactive & policy ─────────────
CONF_MODE_ENV = os.environ.get("MIMIC_FORCE_CONF_MODE", "old").strip().lower()
if CONF_MODE_ENV not in {"old", "new"}:
    CONF_MODE_ENV = "old"

DPKG_FORCE = [
    "-o", "Dpkg::Options::=--force-confdef",
    "-o", f"Dpkg::Options::=--force-conf{'new' if CONF_MODE_ENV == 'new' else 'old'}",
]

APT_ENV = {
    "DEBIAN_FRONTEND": "noninteractive",
    "NEEDRESTART_MODE": "a",            # auto-restart services if needed
    "APT_LISTCHANGES_FRONTEND": "none", # no changelog pager
    "LANG": "C.UTF-8",
    "LC_CTYPE": "C.UTF-8",              # keep LC_ALL out of systemwide config
}

LOCK_WAIT_SECONDS = 300
LOCK_POLL_SECONDS = 3

# ───────────── Root/sudo detection (centralized) ──────────
IS_ROOT = (os.geteuid() == 0) if hasattr(os, "geteuid") else False
HAVE_SUDO = shutil.which("sudo") is not None
SUDO = [] if IS_ROOT else (["sudo"] if HAVE_SUDO else [])

# ─────────────────────── Utilities ────────────────────────
def _print(line: str):
    print(line, flush=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(line + ("\n" if not line.endswith("\n") else ""))
    except Exception:
        pass

def run_command(cmd, env_extra=None, check=True):
    """Run command, stream/tee output, return code."""
    if isinstance(cmd, str):
        popen_args = {"args": cmd, "shell": True}
        pretty = cmd
    else:
        popen_args = {"args": cmd, "shell": False}
        pretty = " ".join(shlex.quote(c) for c in cmd)
    _print(f"$ {pretty}")

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    proc = subprocess.Popen(
        **popen_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    buf = []
    try:
        for line in proc.stdout:
            buf.append(line)
            _print(line.rstrip())
    finally:
        proc.wait()

    if check and proc.returncode != 0:
        _print(f"{RED}Command failed with exit code {proc.returncode}{RESET}")
        e = subprocess.CalledProcessError(proc.returncode, pretty)
        e.output = "".join(buf)
        raise e
    return proc.returncode

def _pids(cmd):
    try:
        out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.DEVNULL).decode().strip()
        return [int(x) for x in out.split() if x.strip().isdigit()]
    except subprocess.CalledProcessError:
        return []

def list_apt_like_pids():
    return set(_pids("pgrep -x apt-get") + _pids("pgrep -x apt") +
               _pids("pgrep -x dpkg") + _pids("pgrep -x unattended-upgrade") +
               _pids("pgrep -x unattended-upgrades"))

def kill_pids(pids):
    if not pids: return
    _print(f"{YELLOW}Attempting to terminate lingering apt/dpkg PIDs: {sorted(pids)}{RESET}")
    run_command(SUDO + ["kill", "-TERM", *map(str, pids)], check=False)
    time.sleep(5)
    still = [p for p in pids if subprocess.call(["ps", "-p", str(p)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0]
    if still:
        _print(f"{YELLOW}Forcing kill of PIDs: {sorted(still)}{RESET}")
        run_command(SUDO + ["kill", "-9", *map(str, still)], check=False)

def wait_for_apt_locks_or_kill(timeout=LOCK_WAIT_SECONDS, poll=LOCK_POLL_SECONDS):
    start = time.time()
    while True:
        others = list_apt_like_pids()
        if not others:
            return
        waited = int(time.time() - start)
        if waited % 15 == 0:
            _print(f"{YELLOW}Waiting for apt/dpkg locks... PIDs: {sorted(others)}  ({waited}s){RESET}")
        if waited >= timeout:
            kill_pids(others); return
        time.sleep(poll)

def repair_dpkg():
    """Repair interrupted dpkg/apt state (fully non-interactive)."""
    _print(f"{YELLOW}Attempting to repair dpkg/apt state...{RESET}")
    dpkg_force = "--force-confnew" if CONF_MODE_ENV == "new" else "--force-confold"
    run_command(SUDO + ["env", *(f"{k}={v}" for k, v in APT_ENV.items()),
                        "dpkg", dpkg_force, "--configure", "-a"], check=False)
    run_command(SUDO + ["env", *(f"{k}={v}" for k, v in APT_ENV.items()),
                        "apt-get", "-yq", "install", "-f"], check=False)

def apt(args_list, retries=2):
    """Run apt-get with non-interactive flags, auto-wait/repair, lean (no recommends)."""
    if isinstance(args_list, str):
        args_list = [args_list]
    wait_for_apt_locks_or_kill()
    base = SUDO + [
        "env", *(f"{k}={v}" for k, v in APT_ENV.items()),
        "apt-get", "-yq",
        "-o", "Acquire::Retries=3",
        "-o", "APT::Install-Recommends=false",
        *DPKG_FORCE,
        *args_list
    ]
    try:
        return run_command(base)
    except subprocess.CalledProcessError as e:
        msg = (getattr(e, "output", "") or "")
        if retries > 0 and ("dpkg was interrupted" in msg or "dpkg --configure -a" in msg or e.returncode == 100):
            repair_dpkg()
            wait_for_apt_locks_or_kill()
            return apt(args_list, retries=retries - 1)
        raise

def pip_install(packages: str):
    """pip install with Bookworm/Trixie system Python compatibility."""
    # Try to keep system pip as-is; just install packages.
    extras = "--no-input --disable-pip-version-check --no-compile"
    try:
        run_command(f"{shlex.quote(sys.executable)} -m pip install {extras} --break-system-packages {packages}")
    except subprocess.CalledProcessError:
        run_command(f"{shlex.quote(sys.executable)} -m pip install {extras} {packages}")

def run_install(packages: str, method: str):
    if method == "apt":
        apt(["install"] + packages.split())
    elif method == "pip":
        pip_install(packages)
    else:
        raise ValueError(f"Unknown install method: {method}")

# ───────────────────── Locales / Runtime dir ─────────────────────
def determine_target_locale() -> str:
    cands = [os.environ.get("LANG","").strip(), os.environ.get("LC_CTYPE","").strip()]
    for cand in cands:
        if cand and cand.lower() not in {"c", "posix"}:
            return cand
    return "en_US.UTF-8"

def ensure_locale(target_locale: str):
    if not target_locale: return
    normalized = target_locale.strip()
    if not normalized: return

    _print("\nEnsuring system locale is configured.")
    _print(f"Target locale: {normalized}")
    run_install("locales", "apt")
    # enable in /etc/locale.gen
    helper = f"""
import pathlib
p = pathlib.Path('/etc/locale.gen')
try: t = p.read_text()
except FileNotFoundError: t = ''
line = {repr(normalized + ' UTF-8')}
if line not in t:
    if '#' + line in t:
        t = t.replace('#' + line, line)
    else:
        if t and not t.endswith('\\n'):
            t += '\\n'
        t += line + '\\n'
    p.write_text(t)
"""
    run_command(SUDO + [shlex.quote(sys.executable), "-c", helper], check=False)
    run_command(SUDO + ["locale-gen", normalized], check=False)
    # Avoid setting LC_ALL systemwide
    run_command(SUDO + ["update-locale", f"LANG={normalized}"], check=False)

def ensure_runtime_dir_permissions():
    """Fix perms on XDG runtime dir if owned by current user."""
    runtime_path = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
    if not runtime_path.exists():
        return
    try:
        st = runtime_path.stat()
    except PermissionError:
        _print(f"{YELLOW}Warning: cannot stat {runtime_path}{RESET}")
        return

    desired_mode = 0o700
    current_mode = stat.S_IMODE(st.st_mode)
    if st.st_uid == os.getuid():
        if current_mode != desired_mode:
            _print("Fixing runtime directory permissions.")
            try:
                runtime_path.chmod(desired_mode)
            except PermissionError:
                run_command(SUDO + ["chmod", "700", str(runtime_path)], check=False)
    else:
        _print(f"{YELLOW}Skipping ownership changes for {runtime_path} (not owned by this user).{RESET}")

# ───────────────────── Convenience helpers ─────────────────────
def needs_reboot() -> bool:
    return os.path.exists("/var/run/reboot-required") or os.path.exists("/run/reboot-required")

def free_repo_space():
    # Scope deletions strictly to the repo root
    for p in list(REPO_ROOT.glob('3D_Printing*')) + [REPO_ROOT / 'Blender']:
        if p.exists() and p.is_dir():
            _print(f"Removing {p}")
            shutil.rmtree(p, ignore_errors=True)

def copy_initial_files():
    _print("\nPopulating initial files (idempotent)")
    try:
        for item in SRC_INITIAL.iterdir():
            dest = DEST_DATA / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    except Exception as e:
        _print(f"{YELLOW}Warning copying initial files: {e}{RESET}")

def run_headless(py_path: Path):
    env = {"MPLBACKEND": "Agg"}
    run_command([shlex.quote(sys.executable), str(py_path)], env_extra=env, check=False)

# ───────────────────────── Main flow ─────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Install ISS Mimic dependencies")
    parser.add_argument("--kivy-from", choices=["pip", "apt"], default="pip",
                        help="Install Kivy from pip (default) or apt")
    parser.add_argument("--skip-prime", action="store_true",
                        help="Skip running data priming scripts at the end")
    args = parser.parse_args()

    _print(f"{CYAN}-------- ISS MIMIC Automatic Install --------{RESET}\n")
    _print(" This install takes between 10–30 minutes on average\n")
    _print(" If you encounter an error, re-run the script. If it persists, open a GitHub issue or ping the Mimic Discord.\n")

    # Pre-flight: ensure network looks sane
    run_command("getent hosts deb.debian.org || true", check=False)

    # Detect distro codename
    try:
        import distro as _distro
        codename = (_distro.codename() or "").lower()
    except Exception:
        codename = ""
    _print(f"Debian/derivative codename: {codename or '(unknown)'}")

    bullseye = "bullseye" in codename
    bookworm = "bookworm" in codename
    trixie   = "trixie"   in codename

    # Logging banner path
    _print(f"Logging to {LOG_PATH}")

    # Prepare env / repair dpkg
    ensure_runtime_dir_permissions()
    wait_for_apt_locks_or_kill()
    repair_dpkg()

    # Full upgrade path
    apt(["update"])
    apt(["full-upgrade"])
    apt(["autoremove"])

    # Locale
    ensure_locale(determine_target_locale())

    # Free some repo space (scoped)
    _print("Freeing optional repo assets to save space")
    free_repo_space()

    # Core packages (lean; common)
    run_install("tzdata ca-certificates git curl wget", "apt")
    run_install("sqlite3 vim", "apt")

    # Python libs via apt (prefer distro wheels where available)
    # Scientific + mapping stack:
    run_install("python3-pandas python3-scipy python3-matplotlib python3-cartopy python3-shapely", "apt")
    # Networking / scraping / misc:
    run_install("python3-requests python3-dateutil python3-serial python3-pil python3-bs4 python3-six", "apt")
    # Twisted/Autobahn (WAMP/TDRS), PyUDev, ephem:
    run_install("python3-twisted python3-autobahn python3-pyudev python3-ephem", "apt")
    # Timezones library (consistent across releases):
    run_install("python3-pytz", "apt")

    # BLAS/LAPACK runtime (no *-dev)
    if bullseye:
        run_install("libatlas3-base", "apt")
    else:
        run_install("libopenblas0-pthread liblapack3", "apt")

    # Kivy runtime libs needed even if using pip wheels
    run_install(
        "libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 "
        "libgl1 libgles2 libmtdev1 libinput10 libjpeg62-turbo libfreetype6 "
        "gstreamer1.0-libav gstreamer1.0-plugins-base",
        "apt",
    )

    # Lightstreamer client (pip)
    pip_install("lightstreamer-client-lib")

    # Kivy itself
    _print("\nInstalling Kivy …")
    if args.kivy_from == "apt":
        run_install("python3-kivy", "apt")
    else:
        pip_install("kivy")
    # Sanity check
    run_command(f"{shlex.quote(sys.executable)} -c 'import kivy, sys; print(\"Kivy\", kivy.__version__); sys.exit(0)'", check=False)

    # Replace Kivy config (safe)
    def replace_kivy_config():
        username = os.environ.get("SUDO_USER") or getuser()
        kivy_cfg = Path(f"/home/{username}/.kivy/config.ini")
        mimic_cfg = REPO_ROOT / "Pi" / "config.ini"
        _print("\nUpdating the Kivy config.ini file.")
        try:
            kivy_cfg.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(mimic_cfg, kivy_cfg)
            _print(f"{GREEN}Kivy config updated at {kivy_cfg}{RESET}")
        except Exception as e:
            _print(f"{YELLOW}Warning: could not replace Kivy config: {e}{RESET}")

    replace_kivy_config()

    # Initial files
    copy_initial_files()

    # Prime data products (headless)
    if not args.skip_prime:
        _print("\nPriming data/products (headless)…")
        run_headless(REPO_ROOT / "Pi" / "getTLE_ISS.py")
        run_headless(REPO_ROOT / "Pi" / "getTLE_TDRS.py")
        run_headless(REPO_ROOT / "Pi" / "NightShade.py")
        run_headless(REPO_ROOT / "Pi" / "orbitGlobe.py")

    # Reboot notice
    if needs_reboot():
        _print(f"{YELLOW}A reboot is required to finish updates (kernel/firmware).{RESET}")
        if os.environ.get("MIMIC_AUTO_REBOOT", "0") == "1":
            _print(f"{YELLOW}Rebooting now (MIMIC_AUTO_REBOOT=1)…{RESET}")
            run_command(SUDO + ["reboot"], check=False)
            return
        else:
            _print(f"{YELLOW}You can reboot now or continue working; changes apply after reboot.{RESET}")

    _print(f"\n{CYAN}-------- Install Complete --------{RESET}")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        _print(f"{RED}Setup failed: {e}{RESET}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        _print(f"\n{YELLOW}Interrupted by user.{RESET}")
        sys.exit(130)
