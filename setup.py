#!/usr/bin/python3

import sys
import subprocess
import argparse

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

def edit_kivy_config(username):
    kivy_config_path = "/home/{}/.kivy/config.ini".format(username)
    lines = []
    to_add = []
    found_mouse_line = False
    found_mtdev_line = False
    found_hid_line = False
    mouse_line = "mouse = mouse"
    mtdev_line = "mtdev_%(name)s = probesysfs,provider=mtdev"
    hid_line = "hid_%(name)s = probesysfs,provider=hidinput"
    in_input_section = False
    with open(kivy_config_path, "r") as f_in:
        for line in f_in:
            lines.append(line)
            if "[input]" in line:
                in_input_section = True
            if "[postproc]" in line:
                in_input_section = False
            if in_input_section:
                if mouse_line in line:
                    found_mouse_line = True
                if mtdev_line in line:
                    found_mtdev_line = True
                if hid_line in line:
                    found_hid_line = True
    if not found_mouse_line:
        to_add.append(mouse_line)
    if not found_mtdev_line:
        to_add.append(mtdev_line)
    if not found_hid_line:
        to_add.append(hid_line)
    input_index = -1
    for x in range(len(lines)):
        if "[input]" in lines[x]:
            input_index = x
    if input_index != -1:
        for x in range(len(to_add)):
            lines.insert(input_index + x + 1, to_add[x] + "\n")
        if to_add:
            print("\nAdding the following lines to the Kivy config:\n{}\n".format("\n".join(to_add)))
            with open(kivy_config_path, 'w') as f_out:
                f_out.writelines(lines)
        else:
            print("\nKivy config is already correct.")
    else:
        print("Not adding anything to the Kivy config.")


def main():
    parser = argparse.ArgumentParser(description='ISS Mimic initial Pi setup tool.')
    parser.add_argument(
            '--skip_kivy', action='store_true',
            help='Skip installing the Kivy package; this is useful if you want to compile it yourself.',
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
        edit_kivy_config(args.username)
    else:
        print("\nSkipping Kivy setup.")

if __name__ == '__main__':
    main()
