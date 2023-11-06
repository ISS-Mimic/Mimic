#!/usr/bin/python3
import os
import distro
import sys
import subprocess
import argparse
import shutil

print("--------ISS MIMIC Automatic Install--------")
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

def run_command(cmd):
    print("{}".format(cmd))
    print((subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)).decode("utf-8"))

def run_install(packages, method):
    if method == "sudo apt-get":
        method = "sudo apt-get -y"
        install_string = "{} install {}".format(method, packages)
        run_command(install_string)
    else:
        install_string = "{} install {} --break-system-packages".format(method, packages)
        try:
            run_command(install_string)
        except Exception as e:
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
    
    username = os.getlogin()
    args = parser.parse_args()

    #Mimic Install Steps

    run_command("sudo apt-get update")
    run_command("sudo apt-get -y upgrade")
    run_command("sudo apt-get -y autoremove")
    run_install("rdate","sudo apt-get")
    run_install("vim", "sudo apt-get") #test editor
    run_install("sqlite3", "sudo apt-get") #telemetry database
    run_install("python3-sdl2", "sudo apt-get") #required for kivy window
    run_install("python3-cartopy", "sudo apt-get") #required for nightshade
    run_install("python3-scipy", "sudo apt-get") #required for nightshade
    run_install("libatlas-base-dev", "sudo apt-get") #fix numpy issue
    run_install("python3-ephem", "sudo apt-get") #python libs for mimic
    if bullseye:
        run_install("pytz", "python -m pip") #python libs for mimic
    else:
        run_install("python3-pytzdata", "sudo apt-get") #python libs for mimic
    run_install("python3-matplotlib", "sudo apt-get") #python libs for mimic
    run_install("python3-pyudev", "sudo apt-get") #python libs for mimic
    run_install("lightstreamer-client-lib", "python -m pip") #iss telemetry service

    print("\nInstalling Kivy requirements and package.")
    if bullseye:
        run_install("kivy", "python -m pip") #iss telemetry service
    else:
        run_install("python3-kivy", "sudo apt-get")
    run_command("python -c 'import kivy'") # run kivy init to create the config.ini file
    print("Replacing Kivy config file")
    replace_kivy_config(username)

    print("fetching ISS TLE to populate initial config file")
    os.system('python Pi/getTLE_ISS.py')
    print("fetching TDRS TLE to populate initial config file")
    os.system('python Pi/getTLE_TDRS.py')
    print("running nightshade to populate the initial orbit map")
    os.system('python Pi/NightShade.py')
    print("running orbitGlobe to populate the initial 3d orbit map")
    os.system('python Pi/orbitGlobe.py')
   
if __name__ == '__main__':
    main()
