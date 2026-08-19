[user] Use web/fetch tools to inspect the GitHub repo aaddrick/claude-desktop-debian (README, build script, latest Releases page). Report: (1) what it does — does it download & repackage the official Windows Claude installer into a .deb? (2) exact install path — is there a PREBUILT .deb in Releases, or must you run build.sh? give the precise commands for Ubuntu 24.04 x86_64, (3) build dependencies it expects, (4) star count and last release/commit date (is it actively maintained mid-2026?), (5) any documented caveats. Be precise with commands.

[assistant] The environment routes network calls through context-mode. Let me load that tool.

[assistant] Excellent, now I have solid release data. Let me fetch the README and build.sh to get the exact commands, dependencies, and caveats.

[assistant] Key finding: since v3.0.0 it repackages the OFFICIAL Linux .deb, not the Windows installer. Let me pull the full README plus building.md and troubleshooting.md in one call, extracting the essential parts compactly.

[assistant] Now the second half with build-from-source, troubleshooting, and acknowledgments.