[user] Independently verify this claimed defect in the GNOME 46 extension. Read the actual file(s) at /home/rempc/jarvis/apps/container-control before deciding. Default to real=false unless you can construct the concrete failure. Confirm the GNOME 46 API facts if the claim depends on them (you may use context7/WebSearch).

CLAIM (lifecycle-leaks):
title: Cleanup method named _onDestroy shadows PanelMenu.Button/ButtonBox base handlers → PopupMenu + whole indicator leak on every disable()
file: /home/rempc/jarvis/apps/container-control/extension.js:104
why: GNOME 46 panelMenu.js:26 (ButtonBox._init) runs `this.connect('destroy', this._onDestroy.bind(this))` at construction. Because `this` is the ContainerIndicator instance, `this._onDestroy` resolves to the SUBCLASS override at extension.js:104, not to PanelMenuButton._onDestroy (panelMenu.js:190) nor ButtonBox._onDestroy (panelMenu.js:89). PanelMenuButton._onDestroy is the ONLY code that calls `this.menu.destroy()`, and ButtonBox._onDestroy is the only code that calls `this.container.destroy()`; both are now shadowed and never run. Concrete scenario: user enables the extension (PopupMenu.actor is parented into Main.uiGroup via setMenu at panelMenu.js:130), then disable() calls this._indicator.destroy(). The subclass _onDestroy runs (twice — once from the base connect, once from the explicit connect at extension.js:90; idempotent so harmless) but the menu is never torn down. The PopupMenu actor stays parented in Main.uiGroup forever, 

[assistant] I'll investigate this claim by reading the actual extension file and verifying the GNOME 46 API facts.

[assistant] Now I need to verify the GNOME 46 `panelMenu.js` source to confirm the base class behavior. Let me fetch the actual source and check the API facts.

[assistant] Let me fetch the actual GNOME 46 panelMenu.js source to verify the base class behavior.

[assistant] Let me fetch the raw source directly via curl to inspect the exact GNOME 46 panelMenu.js.

[assistant] The API facts are confirmed exactly. Now let me verify there's no compensating cleanup in panel.js (e.g., whether `addToStatusArea` / panel destroy handlers destroy the menu or container independently).

[assistant] Let me read the panel.js destroy handler block in full to confirm whether the container/menu get cleaned up independently.

[assistant] I now have full confirmation from the actual GNOME 46 source. Let me consolidate the findings.

**Verified against `gnome-46` branch source (`/tmp/panelMenu46.js`, `/tmp/panel46.js`):**

`panelMenu.js` (ButtonBox base):
- Line 26: `this.connect('destroy', this._onDestroy.bind(this));` — bound in `ButtonBox._init`, which runs during `super._init()`.
- Lines 89-91: `ButtonBox._onDestroy()` → `this.container.child = null; this.container.destroy();`
- Line 132: `setMenu()` → `Main.uiGroup.add_child(this.menu.actor);` (menu actor parented into uiGroup).
- Line 129: `this.menu.connect('open-state-changed', this._onOpenStateChanged.bind(this))` — menu holds a bound-`this` (indicator) ref.
- Lines 190-193: `PanelMenuButton._onDestroy()` → `if (this.menu) this.menu.destroy(); super._onDestroy();` — the ONLY teardown path that destroys the menu.

`panel.js`:
- Lines 931-934: the panel's own `indicator.connect('destroy', ...)` handler ONLY does `delete this.statusArea[role]` and disconnects itself. It does **not** destroy the container, does **not** destroy the menu, and does **not** remove it from the menuManager. So the panel provides zero compensating cleanup.

**JS/GObject shadowing analysis:** When `ButtonBox._init` runs `this._onDestroy.bind(this)`, `this` is the fully-constructed `ContainerIndicator`, so the property lookup resolves to `ContainerIndicator.prototype._onDestroy` (extension.js:104), which shadows `PanelMenuButton.prototype._onDestroy`. The subclass `_onDestroy` (lin