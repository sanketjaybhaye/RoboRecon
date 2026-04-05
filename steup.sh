#!/bin/bash
# RoboRecon v8.0 ULTIMATE setup script
# Installs all dependencies for Kali/Debian-based systems

set -e

echo "🔧 Setting up RoboRecon v8.0 ULTIMATE..."

# Update package lists
echo "📦 Updating package lists..."
sudo apt-get update -qq

# Install Kali/Debian tools
echo "📦 Installing reconnaissance tools..."
sudo apt-get install -y -qq \
    subfinder \
    amass \
    nmap \
    whatweb \
    wafw00f \
    gobuster \
    ffuf \
    dnsutils \
    dirb \
    nikto \
    nuclei \
    httpx \
    openssl \
    jq \
    testssl.sh \
    python3-pip \
    python3-venv \
    whois 2>/dev/null || true

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate it
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install requests lxml colorama DrissionPage -q

echo ""
echo "✅ RoboRecon v8.0 ULTIMATE setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To start using RoboRecon:"
echo ""
echo "  source .venv/bin/activate"
echo "  python3 RoboRecon.py -u example.com --profile standard --html-report"
echo ""
echo "Profiles:"
echo ""
echo "  quick     - robots.txt + sitemap (~5s)"
echo "  standard  - + subdomains, wayback, JS, email, cloud, GraphQL, git, params (~1-2min)"
echo "  deep      - + port scan, vuln scan, takeover, SSL/TLS, whois (~3-5min)"
echo "  nuclear   - deep + dir brute-force + screenshots (~5-15min)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
