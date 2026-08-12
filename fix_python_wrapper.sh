#!/bin/bash
# Create a wrapper for python3 that adds --break-system-packages to pip calls
mv /usr/bin/python3 /usr/bin/python3.orig
cat > /usr/bin/python3 << 'EOF'
#!/bin/bash
if [ "$1" = "-m" ] && [ "$2" = "pip" ] && [ "$3" = "install" ]; then
    exec /usr/bin/python3.orig -m pip install --break-system-packages "${@:4}"
else
    exec /usr/bin/python3.orig "$@"
fi
EOF
chmod +x /usr/bin/python3
echo "Python3 wrapper created"
