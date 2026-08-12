#!/usr/bin/env python3
"""Patch buildozer to skip pip install of dependencies"""

import re

android_py_path = '/usr/local/lib/python3.14/dist-packages/buildozer/targets/android.py'

with open(android_py_path, 'r') as f:
    content = f.read()

old = '''        buildops.cmd(
            [executable, "-m", "pip", "install", "-q", "--break-system-packages", *options, *deps],
            env=self.buildozer.environ)'''

new = '''        # SKIP pip install - deps already installed
        self.logger.info("Dependencies already installed, skipping pip install")
        buildops.cmd(
            [executable, "-c", "import appdirs, colorama, jinja2, sh, meson, ninja, build, toml, packaging, setuptools, wheel; print('All dependencies OK')"],
            env=self.buildozer.environ)'''

if old in content:
    content = content.replace(old, new)
    with open(android_py_path, 'w') as f:
        f.write(content)
    print('Patched successfully!')
else:
    print('Pattern not found!')
    # Show what's actually there
    lines = content.split('\n')
    for i, line in enumerate(lines[774:786], start=775):
        print(f'{i}: {line}')
