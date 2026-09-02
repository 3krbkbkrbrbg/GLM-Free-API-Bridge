#!/usr/bin/env python3
"""
Deploy and run GLM / Z.ai Free API Bridge on Daytona Sandboxes.
Provides cloud execution without needing local resources.
"""

import sys
import os
import time

try:
    from daytona import Daytona, DaytonaConfig
except ImportError:
    print("❌ daytona SDK is not installed. Run: pip install daytona")
    sys.exit(1)

API_KEY = os.environ.get("DAYTONA_API_KEY", "")
if not API_KEY and len(sys.argv) > 1:
    API_KEY = sys.argv[1]

if not API_KEY:
    print("Usage: python3 deploy_daytona.py <DAYTONA_API_KEY> [ZAI_TOKEN]")
    sys.exit(1)

ZAI_TOKEN = ""
if len(sys.argv) > 2:
    ZAI_TOKEN = sys.argv[2]
elif os.path.exists(".secrets/zai_token.txt"):
    with open(".secrets/zai_token.txt", "r") as f:
        ZAI_TOKEN = f.read().strip()

print("⚡ Initializing Daytona Client...")
config = DaytonaConfig(api_key=API_KEY)
daytona = Daytona(config)

print("🚀 Creating / Initializing Sandbox...")
sandbox = daytona.create()
print(f"✅ Sandbox created with ID: {sandbox.id}")

# Clone repo and start service inside sandbox
setup_script = f"""
cd /home/daytona
git clone https://github.com/3krbkbkrbrbg/GLM-Free-API-Bridge.git app 2>/dev/null || (cd app && git pull)
cd /home/daytona/app
mkdir -p .secrets
if [ -n "{ZAI_TOKEN}" ]; then
    echo "{ZAI_TOKEN}" > .secrets/zai_token.txt
fi
export PORT=8080
nohup python3 server.py > server.log 2>&1 &
sleep 2
"""

print("📦 Setting up GLM / Z.ai Bridge inside Sandbox...")
sandbox.process.exec(f"bash -c '{setup_script}'")

# Create signed preview URL (valid for 24h)
print("🌐 Generating 24h Signed Preview URL for Port 8080...")
preview = sandbox.create_signed_preview_url(8080, expires_in_seconds=86400)

print("\n" + "="*60)
print(f"🎉 GLM Free API Bridge is now running on Daytona!")
print(f"🔗 Base URL: {preview.url}/v1")
print(f"📊 Dashboard: {preview.url}/admin")
print("="*60 + "\n")
