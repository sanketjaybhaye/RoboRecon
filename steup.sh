---

### ⚙️ `setup.sh`
```bash
#!/bin/bash
# RoboRecon v6.0 setup script
# Safe environment installer for Kali or Debian-based systems

echo "🔧 Setting up RoboRecon environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip >/dev/null

# Install dependencies
echo "📦 Installing dependencies..."
pip install requests colorama lxml >/dev/null

echo "✅ Setup complete!"
echo "To start using RoboRecon:"
echo "---------------------------------"
echo "source .venv/bin/activate"
echo "python roboRecon_v6.0.py -u example.com"
echo "---------------------------------"
