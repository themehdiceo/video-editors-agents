#!/usr/bin/env bash
# À lancer une seule fois : le bot démarre tout seul à chaque ouverture de session sur le Mac,
# et se met à jour tout seul depuis GitHub. Plus besoin du Terminal ensuite.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$APP_DIR/deploy/run-mac.command" "$APP_DIR/deploy/run-mac.sh"
PLIST="$HOME/Library/LaunchAgents/com.videoeditorsagents.bot.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.videoeditorsagents.bot</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/open</string><string>-a</string><string>Terminal</string>
    <string>$APP_DIR/deploy/run-mac.command</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load -w "$PLIST"
echo "OK : le bot démarre maintenant dans une nouvelle fenêtre, et à chaque ouverture de session."
echo "Tu peux fermer CETTE fenêtre-ci."
