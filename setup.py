#!/usr/bin/python3
"""
ISS Mimic initial Pi setup tool — non‑interactive APT

Changes vs your version:
- Makes APT fully non-interactive (no config prompts) using environment vars and dpkg options.
- Defaults to keeping existing config files ("--force-confold").
- Quiet, resilient run_command with stdout/stderr capture and pretty printing.
- Reuses a common apt() helper so every apt call uses the same safe flags.

If you prefer to always take the maintainer configs instead, set FORCE_CONF_MODE = "new" below.
"""

import os
import distro
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

# ANSI escape codes for some colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'  # Reset color to default

# ---- Behavior toggles ----
# Keep existing config files by default. Set to "new" to prefer package maintainer versions.
FORCE_CONF_MODE = os.environ.get("MIMIC_FORCE_CONF_MODE", "old").lower()  # "old" | "new"

# Build the dpkg options based on the mode.
if FORCE_CONF_MODE not in {"old", "new"}:
    FORCE_CONF_MODE = "old"
DPKG_FORCE = [
    "-o", "Dpkg::Options::=--force-confdef",
    "-o", f"Dpkg::Options::=--force-conf{'old' if FORCE_CONF_MODE=='old' else 'new'}",
]

# Common non-interactive environment (prevents needrestart & listchanges prompts)
APT_ENV = {
    "DEBIAN_FRONTEND": "noninteractive",
    "NEEDRESTART_MODE": "a",           # auto-restart services if needed
    "APT_LISTCHANGES_FRONTEND": "none",
}

# Get the user's home directory
home_dir = Path.home()

# Define the source and destination directories relative to the home directory
source_dir = home_dir / 'Mimic' / 'Pi' / 'InitialFiles'
destination_dir = home_dir / '.mimic_data'

print("double checking correct path for Mimic")
# Define the expected directory name
expected_dir_name = 'Mimic'

# Get the current working directory
current_dir = Path.cwd()

# Check if the current directory name matches the expected name
if current_dir.name != expected_dir_name:
    # Construct the new directory path
    new_dir = current_dir.parent / expected_dir_name

    # Check if a directory with the expected name already exists
    if new_dir.exists():
        print(f"{RED}Error: A directory named '{expected_dir_name}' already exists.{RESET}")
        sys.exit(1)

    # Rename the current directory
    current_dir.rename(new_dir)

    # Optionally, you can change the current working directory to the new path
    os.chdir(new_dir)
else:
    print("Path is correct")

# Create the destination directory if it doesn't exist
destination_dir.mkdir(exist_ok=True)

print(f"{CYAN}--------ISS MIMIC Automatic Install--------{RESET}")
print("\n This install takes between 10-30 minutes on average \n")
print("If you encounter an error, try re-running the script and ensure a stable internet connection. If the problem persists, file an issue on github and/or contact the mimic team on discord")

print("Raspbian distro: " + distro.codename())

if "bullseye" in distro.codename():
    bullseye = True
    print("bullseye detected \n")
else:
    bullseye = False

print("Deleting 3D print folders to free up space")
os.system('rm -rf 3D_Printing*')
os.system('rm -rf Blender')


def run_command(cmd: list[str] | str, env: dict | None = None, check: bool = True) -> int:
    """Run a shell command, stream output live, and return exit code.
    cmd may be a list (recommended) or a shell string. Raises on failure if check=True.
    """
    print(f"{BLUE}$ {' '.join(cmd) if isinstance(cmd, list) else cmd}{RESET}")
    try:
        proc = subprocess.Popen(
            cmd if isinstance(cmd, list) else cmd,
            shell=not isinstance(cmd, list),
            env={**os.environ, **(env or {})},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="")
        rc = proc.wait()
        if check and rc != 0:
            raise subprocess.CalledProcessError(rc, cmd)
        return rc
    except subprocess.CalledProcessError as e:
        print(f"{RED}Command failed with exit code {e.returncode}{RESET}")
        if check:
            sys.exit(e.returncode)
        return e.returncode


def apt(subcmd_and_args: list[str]) -> int:
    """Run apt-get with non-interactive, safe defaults everywhere."""
    base = [
        "sudo",
        "env",
        *(f"{k}={v}" for k, v in APT_ENV.items()),
        "apt-get",
        "-yq",  # assume-yes + quiet
        *DPKG_FORCE,
    ]
    return run_command(base + subcmd_and_args)


def run_install(packages: str, method: str):
    if method == "sudo apt-get":
        # Use apt() so the same non-interactive flags apply to installs
        pkgs = packages.split()
        apt(["install", *pkgs])
    else:
        # pip install path; try with --break-system-packages first, fall back if needed
        install_cmd = ["python", "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "--upgrade"]
        # allow caller to pass arbitrary method like "python -m pip"
        if method.strip() != "python -m pip":
            # Respect custom methods; still add non-interactive flags if it's pip
            pass
        try:
            run_command(["python", "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "--upgrade", "--break-system-packages", *packages.split()])
        except SystemExit:
            # Fallback without --break-system-packages
            run_command(["python", "-m", "pip", "install", "--no-input", "--disable-pip-version-check", "--upgrade", *packages.split()])


def replace_kivy_config(username):
    kivy_config_path = f"/home/{username}/.kivy/config.ini"
    mimic_config_path = f"/home/{username}/Mimic/Pi/config.ini"
    print("\nUpdating the Kivy config.ini file.")
    shutil.copyfile(mimic_config_path, kivy_config_path)


def main():
    parser = argparse.ArgumentParser(description='ISS Mimic initial Pi setup tool.')
    parser.add_argument(
        '--skip_kivy', action='store_true',
        help='Skip installing the Kivy package and replacing the Kivy config file.',
        default=False)

    username = os.getlogin()
    args = parser.parse_args()

    # Mimic Install Steps
    apt(["update"])  # refresh package index
    apt(["upgrade"])  # keep existing configs (or maintainer if FORCE_CONF_MODE="new")
    apt(["autoremove"])  # cleanup

    run_install("rdate", "sudo apt-get")
    run_install("vim", "sudo apt-get")  # test editor
    run_install("sqlite3", "sudo apt-get")  # telemetry database
    run_install("python3-sdl2", "sudo apt-get")  # required for kivy window
    run_install("python3-cartopy", "sudo apt-get")  # required for nightshade
    run_install("python3-scipy", "sudo apt-get")  # required for nightshade
    run_install("python3-pandas", "sudo apt-get")  # NASA VV correlation
    run_install("libatlas-base-dev", "sudo apt-get")  # fix numpy issue
    run_install("python3-twisted", "sudo apt-get")  # websocket deps
    run_install("python3-autobahn", "sudo apt-get")  # websocket deps
    run_install("python3-ephem", "sudo apt-get")  # python libs for mimic
    if "bullseye" in distro.codename():
        run_install("pytz", "python -m pip")  # python libs for mimic
    else:
        run_install("python3-pytzdata", "sudo apt-get")  # python libs for mimic
    run_install("python3-matplotlib", "sudo apt-get")
    run_install("python3-pyudev", "sudo apt-get")
    run_install("lightstreamer-client-lib", "python -m pip")  # iss telemetry service

    # Kivy install
    print("\nInstalling Kivy requirements and package.")
    if "bullseye" in distro.codename():
        run_install("kivy", "python -m pip")
    else:
        run_install("kivy", "python -m pip")
    run_command("python -c 'import kivy'", check=False)  # run kivy init to create config.ini
    print("Replacing Kivy config file")
    replace_kivy_config(username)

    print("")
    print("Populating initial files just in case they don't update")
    # Copy all files and directories from source to destination
    for item in source_dir.iterdir():
        dest = destination_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    print("fetching ISS TLE to populate initial config file")
    os.system('python Pi/getTLE_ISS.py')
    print("fetching TDRS TLE to populate initial config file")
    os.system('python Pi/getTLE_TDRS.py')
    print("running nightshade to populate the initial orbit map")
    os.system('python Pi/NightShade.py')
    print("running orbitGlobe to populate the initial 3d orbit map")
    os.system('python Pi/orbitGlobe.py')
    print(f"{CYAN}--------Install Complete--------{RESET}")


if __name__ == '__main__':
    main()
