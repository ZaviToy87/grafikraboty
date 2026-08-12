#!/bin/bash
mv /usr/bin/pip3 /usr/bin/pip3.orig
cat > /usr/bin/pip3 << 'EOF'
#!/bin/bash
/usr/bin/pip3.orig --break-system-packages "$@"
EOF
chmod +x /usr/bin/pip3
echo "Pip wrapper created"
