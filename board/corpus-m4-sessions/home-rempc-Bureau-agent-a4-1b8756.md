[user] You are a skeptical supply-chain security reviewer. The likely recommendation for installing Claude Desktop on Ubuntu 24.04 is the community repo aaddrick/claude-desktop-debian, which repackages Anthropic's official Windows installer into a .deb.

Survey findings:
[
  {
    "officialLinux": "yes — As of July 2026, Anthropic DOES ship an OFFICIAL native Linux desktop app, but it is in BETA. It was released ~2026-06-30. Officially supported platforms for the desktop app: macOS, Windows (x64 + arm64), and Linux (beta). ChromeOS is served via the Android/Play app. For Linux, the ONLY officially shipped package format is .deb (Debian/Ubuntu), for amd64 and arm64, delivered from Anthropic's own APT repository. Official Linux requirements: Ubuntu 22.04+ or Debian 12+, x86_64 or arm64. Anthropic explicitly states Fedora and RHEL are NOT supported (\"only Debian-based distributions are supported today\"). There is NO official rpm, AppImage, Flatpak, or Snap. Official Linux docs/download entry point: https://code.claude.com/docs/en/desktop-linux (linked as \"Download for Linux / See docs\" from https://claude.com/download). Official APT repo base: https://downloads.claude.ai/claude-desktop/apt/stable ; signing key: https://downloads.claude.ai/claude-desktop/key.asc",
    "methods": [
      {
        "name": "Claude Desktop (Linux beta) via Anthropic official APT repository — RECOMMENDED",
        "channel": "official",
        "installCommands": "sudo apt install curl\nsudo curl -fsSLo

[assistant] I'll assess this adversarially. Let me first try to verify the key claims that change everything here, especially whether Anthropic now ships an official Linux .deb (which would make the community repo unnecessary for a security-conscious user).

[assistant] Network works. Let me verify the load-bearing claims: (1) does Anthropic actually ship an official Linux .deb now, and (2) what the aaddrick repo actually does today.

[assistant] A context-mode interceptor wants me to route network fetches through it. Let me load and use it.

[assistant] The GitHub facts check out (5,283 stars, Apache-2.0, v3.2.1+claude1.24012.9, build.sh explicitly repackages the official Linux .deb, not the Windows installer). The third check got auto-indexed. Let me re-run the official-repo existence check with small output, and inspect the exact fetch+SHA-pin logic.