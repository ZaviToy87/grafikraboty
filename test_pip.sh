#!/bin/bash
cd /home/buildozer_project
python3 -m pip install -q --break-system-packages 'sh>=2, <3.0; sys_platform!="win32"'
echo "EXIT: $?"
