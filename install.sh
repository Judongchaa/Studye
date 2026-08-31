#!/bin/bash
set -e

echo "==================================="
echo "  Installing Studye System-Wide  "
echo "==================================="

# 1. Get the absolute path where the user cloned the repository
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[*] Studye directory: $DIR"

# 2. Setup the Python Virtual Environment
if [ ! -d "$DIR/venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv "$DIR/venv"
fi

echo "[*] Installing dependencies..."
source "$DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$DIR/requirements.txt"

# 3. Create a global command to run 'studye' from anywhere
mkdir -p ~/.local/bin
WRAPPER=~/.local/bin/studye
echo "[*] Creating executable shortcut at $WRAPPER..."

cat <<EOF > "$WRAPPER"
#!/bin/bash
# Automatically uses the virtual environment and passes all arguments
# cd into the project directory so relative config paths resolve correctly
cd "$DIR"
source "$DIR/venv/bin/activate"
python "$DIR/main.py" "\$@"
EOF

chmod +x "$WRAPPER"

echo "==================================="
echo "       Installation Complete!      "
echo "==================================="
echo "-> You can now open a terminal anywhere and type: studye"
echo "Make sure ~/.local/bin is in your system PATH!"
