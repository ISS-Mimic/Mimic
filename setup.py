#!/usr/bin/python3

import sys
import subprocess
import argparse
import shutil

def run_command(cmd):
    print("{}".format(cmd))
    result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    output = result.decode("utf-8")
    output = output.strip()
    return output

def run_install(packages, method):
    if method == "sudo apt-get":
        method = "sudo apt-get -y"
    install_string = "{} install {}".format(method, packages)
    run_command(install_string)

def replace_kivy_config(username):
    kivy_config_path = "/home/{}/.kivy/config.ini".format(username)
    mimic_config_path = "/home/{}/Mimic/Pi/config.ini".format(username)
    print("\nUpdating the Kivy config.ini file.")
    shutil.copyfile(mimic_config_path, kivy_config_path)

def main():
    parser = argparse.ArgumentParser(description='ISS Mimic initial Pi setup tool.')
    parser.add_argument(
            '--skip_kivy', action='store_true',
            help='Skip installing the Kivy package and replacing the Kivy config file.',
            default=False)
    parser.add_argument(
            '--username', type=str,
            help='Specify Pi username (default is pi).',
            default="pi")

    args = parser.parse_args()

    print("\nBefore running this script, you should make sure your packages are updated.")
    print("If you still need to do that, Ctrl+C this script to exit and run the following:")
    print("sudo apt -y update; sudo apt -y upgrade\n")

    run_install("vim", "sudo apt-get")
    run_install("python3-numpy", "sudo apt-get")
    run_install("nodejs sqlite3", "sudo apt-get")
    run_command("curl https://www.npmjs.com/install.sh | sudo sh")
    run_install("lightstreamer-client", "npm")
    run_install("sqlite3", "npm")
    run_install("ephem pytz matplotlib autobahn twisted pyudev", "python3 -m pip")
    run_install("python3-mpltoolkits.basemap --fix-missing", "sudo apt-get")

    if not args.skip_kivy:
        print("\nInstalling Kivy requirements and package.")
        kivy_packages = "libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev pkg-config libgl1-mesa-dev libgles2-mesa-dev python3-setuptools libgstreamer1.0-dev git-core gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-omx gstreamer1.0-alsa python3-dev libmtdev-dev xclip xsel libjpeg-dev"
        run_install(kivy_packages, "sudo apt-get")
        run_install("--upgrade --user pip setuptools", "python3 -m pip")
        run_install("--upgrade --user Cython==0.29.10 pillow", "python3 -m pip")
        run_install("--user kivy", "python3 -m pip")
        run_command("python3 -c 'import kivy'") # run kivy init to create the config.ini file
        replace_kivy_config(args.username)
    else:
        print("\nSkipping Kivy setup.")

if __name__ == '__main__':
    main()
