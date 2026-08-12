#!/bin/bash
cd '/mnt/c/Users/User/Desktop/GrafikRaboty/GrafikRaboty/mobile_app'
buildozer android debug > /tmp/buildozer_output.log 2>&1
echo "EXIT_CODE=$?" >> /tmp/buildozer_exit.txt
