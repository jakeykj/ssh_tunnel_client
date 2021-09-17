"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""
import os
from shutil import copyfile
from setuptools import setup

APP = ['tunnels.py']
DATA_FILES = ['config_template.yaml', 'green_dot.png', 'red_dot.png', 'icon_on.png', 'icon_off.png']
OPTIONS = {
    'packages': ['rumps'],
    'iconfile':'tunnel.icns',
    'plist': {'CFBundleShortVersionString':'0.1.0'}
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)