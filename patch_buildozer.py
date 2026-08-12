import re
with open('/usr/local/lib/python3.14/dist-packages/buildozer/targets/android.py', 'r') as f:
    content = f.read()
content = content.replace('options = ["--user"]', 'options = []')
with open('/usr/local/lib/python3.14/dist-packages/buildozer/targets/android.py', 'w') as f:
    f.write(content)
print('Patched successfully')
