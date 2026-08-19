[user] Independently verify this claimed defect in the GNOME 46 extension. Read the actual file(s) at /home/rempc/jarvis/apps/container-control before deciding. Default to real=false unless you can construct the concrete failure. Confirm the GNOME 46 API facts if the claim depends on them (you may use context7/WebSearch).

CLAIM (lifecycle-leaks):
title: Confirmation ModalDialog is untracked; disabling while a confirm dialog is open orphans it and keeps the destroyed indicator alive
file: /home/rempc/jarvis/apps/container-control/extension.js:343
why: _confirm() creates a ModalDialog that is registered on the Shell's modal stack, not stored on the indicator, and disable() (line 378) only calls this._indicator.destroy() — it never closes open dialogs. Scenario: user opens the 'Tout arrêter ?' / group confirm dialog, then the extension is disabled (update, Extensions toggle, Wayland lock). The indicator is destroyed but the dialog stays on screen; its onConfirm closure retains the now-destroyed indicator (`this`), and if the user then clicks Confirm it calls containerAction()/_scheduleSettleRefresh() against a nulled this._cancellable. It does not crash (the this._destroyed guards no-op the UI paths and a null cancellable is legal for the subprocess), but it leaves an orphaned modal and pins the dead indicator until the dialog is dismissed. Lower severity because it requires a dialog to be open at the exact moment of disable.
proposed fix: Track the active dialog (e.g. this._dialog = 

[assistant] Let me examine the supporting library files and verify the GNOME 46 ModalDialog API behavior.

[assistant] I've now verified all the technical facts. Let me confirm my analysis of each claim point.

**File facts (verified):**
- Line 343-365 `_confirm()`: creates `const dialog = new ModalDialog.ModalDialog(...)` — a local variable, never stored on `this`. Confirmed untracked.
- Line 104-116 `_onDestroy()`: sets `_destroyed`, removes timeout/oneShots, cancels+nulls `_cancellable`. It does NOT reference or close any dialog. Confirmed.
- Line 378-381 `disable()`: only calls `this._indicator?.destroy()` (which fires the `destroy` signal → `_onDestroy()`) then nulls the indicator. No dialog handling. Confirmed.

**GNOME 46 API facts:**
- `ModalDialog.ModalDialog` is not a child of the `PanelMenu.Button`. On `open()` it adds its actor to the shell's persistent UI group and calls `Main.pushModal()` to take an input grab. Destroying the panel-button indicator therefore does NOT destroy or close the dialog — it remains on screen holding its modal grab. This is standard, well-established GNOME Shell behavior.

**Crash / null-cancellable path (verified in docker.js):**
- `run()` at line 22/33 passes `cancellable` straight to `communicate_utf8_async(null, cancellable, ...)`; the header comment explicitly says "`cancellable` may be null," and a null `GCancellable` is legal for GIO async calls. So clicking "Confirmer" on the orphaned dialog after disable issues `containerAction(name, verb, null, cb)` without crashing.
- `_scheduleSettleRefresh()` (line 138) no-ops: `_refresh()` early-returns on 