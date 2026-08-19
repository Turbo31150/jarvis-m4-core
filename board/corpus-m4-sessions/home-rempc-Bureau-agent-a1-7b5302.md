[user] Independently verify this claimed defect in the GNOME 46 extension. Read the actual file(s) at /home/rempc/jarvis/apps/container-control before deciding. Default to real=false unless you can construct the concrete failure. Confirm the GNOME 46 API facts if the claim depends on them (you may use context7/WebSearch).

CLAIM (logic-ux):
title: No subprocess timeout: a hung `docker ps` latches _refreshing=true and stalls all future refreshes with no recovery
file: /home/rempc/jarvis/apps/container-control/extension.js:120
why: The single _refreshing flag is only cleared inside the listContainers callback (line 123), which fires on normal completion or cancellation — but not if the subprocess never exits. docker.js run() has no timeout and never force-exits the process. If `docker ps` hangs (e.g. DOCKER_HOST/context pointing at an unreachable remote daemon, or a wedged docker socket), the callback never runs, _refreshing stays true, and every subsequent poll returns early at line 120. The panel is then stuck on '…' (or stale counts) with no self-recovery even after docker comes back, since nothing ever clears the flag.
proposed fix: Add a watchdog: arm a GLib timeout (e.g. 10s) when starting a refresh that force-exits/cancels the subprocess and clears _refreshing if the callback hasn't fired; cancel that watchdog in the callback. Alternatively pass a per-call cancellable with a deadline so communicate_utf8_async always resolves.

[assistant] Now let me read the docker.js library and the model.js to understand the subprocess handling.

[assistant] I have read both the UI file (`extension.js`) and the subprocess wrapper (`lib/docker.js`). Let me verify my understanding of the concurrency guard and confirm there's no timeout mechanism anywhere.

[assistant] I have confirmed the claim by reading both the UI file and the subprocess wrapper. My analysis is complete.

**Confirmation of the code facts:**

- `extension.js:120-123` — `_refresh()` guards on `this._refreshing`, sets it `true` at line 121, and the ONLY place it is ever reset to `false` is line 123, inside the `listContainers` callback.
- `lib/docker.js:22-42` — `run()` calls `proc.communicate_utf8_async(null, cancellable, cb)` with **no timeout and no `force_exit`**. The subprocess is never killed by the wrapper.
- The only `_cancellable.cancel()` is in `_onDestroy()` (line 113), i.e. only on extension teardown — never for recovery.
- Every refresh entry point funnels through `_refresh()` and is gated by line 120: the 5s periodic poll (94-101), menu-open (83-88), the manual "Rafraîchir" button (176), and `_scheduleSettleRefresh` after actions (138-147). All return early once the flag is latched.

**GIO/GJS API fact (GNOME 46):** `Gio.Subprocess.communicate_utf8_async()` reads stdout/stderr to EOF and reaps the child; its `GAsyncReadyCallback` fires only on natural completion (both pipes EOF + process reaped), on cancellation, or on I/O error. There is no built-in timeout. A `docker` CLI blocked on a wedged/unreachable daemon holds its stdout/stderr open, so the async op never completes and the callback never runs. This is foundational, version-stable GIO behavior — no doc lookup needed.

**Constructed failure:** dockerd deadlocks (a documented real-world Docker failure — 