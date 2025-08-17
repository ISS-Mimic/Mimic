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
            return
        waited = int(time.time() - start)
        if waited % 15 == 0:
            print(f"{YELLOW}Waiting for apt/dpkg locks... PIDs: {sorted(others)}  ({waited}s){RESET}")
        if waited >= timeout:
            kill_pids(others); return
        time.sleep(poll)


def repair_dpkg():
    """Repair interrupted dpkg/apt state (fully non-interactive)."""
    print(f"{YELLOW}Attempting to repair dpkg/apt state...{RESET}")
    # dpkg itself must receive --force-confold/--force-confnew for conffiles
    dpkg_force = "--force-confnew" if CONF_MODE_ENV == "new" else "--force-confold"
    run_command(["sudo", "env", *(f"{k}={v}" for k, v in APT_ENV.items()),
                 "dpkg", dpkg_force, "--configure", "-a"], check=False)
    run_command(["sudo", "env", *(f"{k}={v}" for k, v in APT_ENV.items()),
                 "apt-get", "-yq", "install", "-f"], check=False)


def apt(args_list, retries=1):
    """Run apt-get with non-interactive flags, auto-wait/kill locks, auto-repair once."""
    if isinstance(args_list, str):
        args_list = [args_list]

    wait_for_apt_locks_or_kill()

    base = [
        "sudo", "env",
        *(f"{k}={v}" for k, v in APT_ENV.items()),
        "apt-get", "-yq",
        "-o", "Acquire::Retries=3",
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
    """pip install that works on Bookworm system Python."""
    try: run_command("python3 -m pip install --upgrade pip")
    except Exception: pass
    try:
        run_command(f"python3 -m pip install --no-input --disable-pip-version-check --break-system-packages {packages}")
    except subprocess.CalledProcessError:
        run_command(f"python3 -m pip install --no-input --disable-pip-version-check {packages}")


def run_install(packages: str, method: str):
    if method == "apt":
        apt(["install"] + packages.split())
    elif method == "pip":
        pip_install(packages)
    else:
        raise ValueError(f"Unknown install method: {method}")


def replace_kivy_config(username):
    kivy_config_path = f"/home/{username}/.kivy/config.ini"
    mimic_config_path = f"/home/{username}/Mimic/Pi/config.ini"
    print("\nUpdating the Kivy config.ini file.")
    try:
        Path(kivy_config_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(mimic_config_path, kivy_config_path)
        print(f"{GREEN}Kivy config updated at {kivy_config_path}{RESET}")
    except Exception as e:
        print(f"{YELLOW}Warning: could not replace Kivy config: {e}{RESET}")


def needs_reboot() -> bool:
    return os.path.exists("/var/run/reboot-required") or os.path.exists("/run/reboot-required")


# ───────────────────────── Main flow ─────────────────────────
def main():
    print("double checking correct path for Mimic")
    expected_dir_name = 'Mimic'
    current_dir = Path.cwd()
    if current_dir.name != expected_dir_name:
        new_dir = current_dir.parent / expected_dir_name
        if new_dir.exists():
            print(f"{RED}Error: A directory named '{expected_dir_name}' already exists.{RESET}")
            sys.exit(1)
        current_dir.rename(new_dir); os.chdir(new_dir)
    else:
        print("Path is correct")

    destination_dir.mkdir(exist_ok=True)

    print(f"{CYAN}--------ISS MIMIC Automatic Install--------{RESET}\n")
    print(" This install takes between 10-30 minutes on average \n")
    print("If you encounter an error, try re-running the script and ensure a stable internet connection. "
          "If the problem persists, file an issue on github and/or contact the mimic team on discord")
    print("Raspbian distro: " + distro.codename())
    bullseye = ("bullseye" in distro.codename())
    if bullseye: print("bullseye detected \n")

    # Free some space
    print("Deleting 3D print folders to free up space")
    os.system('rm -rf 3D_Printing*'); os.system('rm -rf Blender')

    username = os.environ.get("SUDO_USER") or getuser()

    # PRE-FLIGHT: ensure no broken state / locks before apt
    wait_for_apt_locks_or_kill()
    repair_dpkg()  # ensures dpkg is clean and non-interactive

    # APT core flow (full-upgrade for kernel/firmware too)
    apt(["update"])
    apt(["full-upgrade"])
    apt(["autoremove"])

    # Packages
    run_install("rdate", "apt")
    run_install("vim", "apt")
    run_install("sqlite3", "apt")
    run_install("python3-sdl2", "apt")
    run_install("python3-cartopy", "apt")
    run_install("python3-scipy", "apt")
    run_install("python3-pandas", "apt")
    run_install("libatlas-base-dev", "apt")
    run_install("python3-twisted", "apt")
    run_install("python3-autobahn", "apt")
    run_install("python3-ephem", "apt")
    if bullseye:
        run_install("pytz", "pip")
    else:
        run_install("python3-pytzdata", "apt")
    run_install("python3-matplotlib", "apt")
    run_install("python3-pyudev", "apt")
    run_install("lightstreamer-client-lib", "pip")

    # Kivy
    print("\nInstalling Kivy requirements and package.")
    run_install("kivy", "pip")
    try:
        run_command("python3 -c 'import kivy; print(kivy.__version__)'")
    except Exception: pass

    print("Replacing Kivy config file")
    replace_kivy_config(username)

    # Populate initial files
    print("\nPopulating initial files just in case they don't update")
    try:
        for item in source_dir.iterdir():
            dest = destination_dir / item.name
            if item.is_dir(): shutil.copytree(item, dest, dirs_exist_ok=True)
            else:             shutil.copy2(item, dest)
    except Exception as e:
        print(f"{YELLOW}Warning copying initial files: {e}{RESET}")

    # Prime data products
    print("fetching ISS TLE to populate initial config file")
    run_command('python3 Pi/getTLE_ISS.py', check=False)

    print("fetching TDRS TLE to populate initial config file")
    run_command('python3 Pi/getTLE_TDRS.py', check=False)

    print("running nightshade to populate the initial orbit map")
    run_command('python3 Pi/NightShade.py', check=False)

    print("running orbitGlobe to populate the initial 3d orbit map")
    run_command('python3 Pi/orbitGlobe.py', check=False)

    # Reboot notice / auto-reboot
    if needs_reboot():
        print(f"{YELLOW}A reboot is required to finish updates (kernel/firmware).{RESET}")
        if os.environ.get("MIMIC_AUTO_REBOOT", "0") == "1":
            print(f"{YELLOW}Rebooting now (MIMIC_AUTO_REBOOT=1)...{RESET}")
            run_command("sudo reboot", check=False)
            return
        else:
            print(f"{YELLOW}You can reboot now or continue working; changes apply after reboot.{RESET}")

    print(f"{CYAN}--------Install Complete--------{RESET}")


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"{RED}Setup failed: {e}{RESET}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user.{RESET}")
        sys.exit(130)
