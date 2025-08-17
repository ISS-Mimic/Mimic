#!/usr/bin/python3
import os
import sys
import time
import shlex
import distro
import argparse
import shutil
import subprocess
from pathlib import Path
from getpass import getuser

# ───────────────────────── Colors ─────────────────────────
RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
BLUE = '\033[94m'; CYAN = '\033[96m'; RESET = '\033[0m'

# ───────────────────────── Paths ──────────────────────────
home_dir = Path.home()
source_dir = home_dir / 'Mimic' / 'Pi' / 'InitialFiles'
destination_dir = home_dir / '.mimic_data'

# ─────────────── Apt non-interactive & policy ─────────────
# "old" keeps local config files; "new" takes maintainer versions
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
}

LOCK_WAIT_SECONDS = 300  # 5 minutes before killing lock holders
LOCK_POLL_SECONDS = 3

# ─────────────────────── Utilities ────────────────────────
def run_command(cmd, env_extra=None, check=True):
    """Run a command, stream output live, return exit code (raise if check=True and nonzero)."""
    if isinstance(cmd, str):
        popen_args = {"args": cmd, "shell": True}
        pretty = cmd
    else:
        popen_args = {"args": cmd, "shell": False}
        pretty = " ".join(shlex.quote(c) for c in cmd)
    print(f"$ {pretty}", flush=True)

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
            print(line.rstrip())
    finally:
        proc.wait()

    if check and proc.returncode != 0:
        print(f"{RED}Command failed with exit code {proc.returncode}{RESET}")
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
    print(f"{YELLOW}Attempting to terminate lingering apt/dpkg PIDs: {sorted(pids)}{RESET}")
    run_command(["sudo", "kill", "-TERM"] + [str(p) for p in pids], check=False)
    time.sleep(5)
    still = [p for p in pids if subprocess.call(["ps", "-p", str(p)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0]
    if still:
        print(f"{YELLOW}Forcing kill of PIDs: {sorted(still)}{RESET}")
        run_command(["sudo", "kill", "-9"] + [str(p) for p in still], check=False)


def wait_for_apt_locks_or_kill(timeout=LOCK_WAIT_SECONDS, poll=LOCK_POLL_SECONDS):
    start = time.time()
    while True:
        others = list_apt_like_pids()
        if not others:
