import re

filepath = '/usr/local/lib/python3.14/dist-packages/buildozer/targets/android.py'
with open(filepath, 'r') as f:
    content = f.read()

# Find the line with pip install command and add --break-system-packages
old = '''        buildops.cmd(
            [executable, "-m", "pip", "install", "-q", *options, *deps],'''

new = '''        buildops.cmd(
            [executable, "-m", "pip", "install", "-q", "--break-system-packages", *options, *deps],'''

content = content.replace(old, new)

with open(filepath, 'w') as f:
    f.write(content)
print('Patched successfully')
