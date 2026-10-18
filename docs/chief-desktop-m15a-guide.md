# Chief desktop (M1.5A): setup and live checks

This guide sets up **Chief**, a small window that stays open while you work in other apps. Chief is a
client of `cos`. It shows what `cos` returns and asks `cos` to act. All decisions stay in `cos`.

Every command below is meant to be copied and pasted into Terminal. Steps in **bold** are clicks.

---

## 0. Before you start

- Worktree: `~/Projects/taw-cos-m1`, branch `feature/cos-m15a`.
- Ollama is running, and `cos` works on its own:

  ```bash
  cd ~/Projects/taw-cos-m1
  bin/cos status
  bin/cos ask "what time is it"
  ```

  `status` should end with `Ollama reachable`. If it says `unreachable`, open Ollama first.

---

## 1. Install

```bash
cd ~/Projects/taw-cos-m1/apps/chief-desktop
npm ci
npm run typecheck && npm test && npm run build
```

Expected: `pass 18`, `fail 0`, and `static checks: … passed, 0 failed`.

`npm ci` reports that `electron-winstaller` (Windows only) has an install script that isn't
allowed. That's expected. Don't approve it, because the Mac build doesn't need it.

---

## 2. Dev run (optional)

```bash
cd ~/Projects/taw-cos-m1/apps/chief-desktop
npm run dev
```

- The first run downloads the Electron binary (about 100 MB) once.
- The Chief window opens. A ring icon appears in the menu bar.
- Hot reload is off, because the security policy blocks its connection. To see an edit,
  press **⌘R** in the window.
- **To stop:** press **⌘Q** in Chief, or **Control-C** in Terminal. Either one stops the dev
  server too.

---

## 3. Package and sign with your identity

Your signing identity is the Apple Development certificate with SHA-1
`1BA6ECA08FD8D21A979A33AF42296F96A9E93885`. Two certificates share the same name, so use the
SHA-1 to choose exactly this one.

```bash
cd ~/Projects/taw-cos-m1/apps/chief-desktop
CSC_NAME=1BA6ECA08FD8D21A979A33AF42296F96A9E93885 npm run package
```

If macOS asks to allow `codesign` to use the key, click **Always Allow** (or **Allow**).

Check the signature:

```bash
codesign -dv --verbose=2 release/mac-arm64/Chief.app 2>&1 | grep -E "Identifier|Authority|TeamIdentifier|flags"
codesign --verify --deep --strict release/mac-arm64/Chief.app && echo SIGNATURE-OK
```

Expected:
- `Identifier=local.chief-of-staff.desktop`
- `Authority=Apple Development: …`
- `TeamIdentifier=KXYQ8895ZL`
- `flags=0x10000(runtime)` (hardened runtime)
- `SIGNATURE-OK`

There is no notarization and no auto-update.

---

## 4. Move Chief.app to /Applications

```bash
rm -rf /Applications/Chief.app
ditto ~/Projects/taw-cos-m1/apps/chief-desktop/release/mac-arm64/Chief.app /Applications/Chief.app
```

---

## 5. First launch and Gatekeeper

1. In Finder, open **Applications** and double-click **Chief**.
2. You built the app on this Mac, so it has no quarantine flag, and Gatekeeper normally doesn't
   ask. If macOS still says it "can't be opened":
   1. Open **System Settings → Privacy & Security**.
   2. Scroll to **Security** and click **Open Anyway** next to "Chief was blocked".
   3. Confirm with **Open**.
3. Expected:
   - The Chief window appears (about 380×540).
   - A ring icon appears in the menu bar.
   - The dot at the top left turns green and says **Ready**.

Chief needs no Privacy permissions: no Accessibility, Screen Recording, camera, microphone, or
notifications. If macOS asks for one, click **Don't Allow** and tell Claude.

---

## 6. Set cosPath (only if needed)

By default, Chief runs `~/Projects/taw-cos-m1/bin/cos`. If that file is missing, every request
shows **"Chief isn't set up yet: cos was not found at …"**.

To point Chief at another `cos` (for example, after the branch is merged into the main checkout):

```bash
mkdir -p ~/Library/Application\ Support/ChiefOfStaff
cat > ~/Library/Application\ Support/ChiefOfStaff/desktop.json <<'EOF'
{
  "cosPath": "~/Projects/teacher-ai-workstation/bin/cos",
  "hotkey": "Control+Alt+C"
}
EOF
```

Then quit Chief (**menu bar ring → Quit Chief**) and open it again. Both keys are optional.
`hotkey` uses Electron accelerator names, where **Alt** means Option.

---

## 7. Live checks

Do these in order. Write down anything that doesn't match.

### Classroom projector (read first)

Screen protection keeps Chief out of screenshots, recordings, and screen sharing. A projector
that **mirrors** your screen over HDMI or USB-C shows the screen directly, so Chief can appear on
it. Before teaching, do one of these:

- **Hide Chief before you connect.** Press **⌃⌥C** (Control-Option-C) until Chief is hidden, then
  connect the projector. If Chief is behind another window, the first press brings it to the
  front and the second press hides it. Press **⌃⌥C** again only when the projector is off or disconnected.
- **Or use the projector as an extended display.** Open **System Settings → Displays**, select
  the projector, and set **Use as:** to **Extended display**. Keep Chief on the Mac's built-in
  screen. The projector then shows only what you drag onto it.

Check 7.8 tests this with a real mirrored display.

### 7.1 Hotkey
1. Click into another app, such as Safari.
2. Press **⌃⌥C** (Control-Option-C). Chief comes to the front with the cursor in the input.
3. Press **⌃⌥C** again. Chief hides.
4. Press **Escape** while Chief is focused. Chief hides.
5. If the hotkey does nothing, click the menu bar ring. The menu's first line should say
   **"Hotkey Control+Alt+C could not be registered"**. Another app may own that shortcut.
   Choose another one in `desktop.json` (step 6).

### 7.2 Ask and history
1. Type `what time is it` and press **Enter**.
   - Expected: an answer on the left. The footer reads **fast path (no model) · Tools: time.now · N ms**.
2. Type `Give me one tip for a calm classroom transition`, then press **Shift-Enter** and type a
   second line. The input grows. Press **Enter**.
   - Expected: the dot turns amber, the input shows **Thinking…**, and then an answer appears.
     The footer shows the model name (for example `qwen3.6:35b`), the tools used, and the time.
3. Click **Copy** under an answer and paste it in Notes. The text should match.
4. Quit Chief with **⌘Q** and open it again. Both turns are still there.
5. Scroll up in the feed and ask another question. The feed shouldn't jump while you are
   scrolled up. Scroll back to the bottom, and new answers scroll into view again.
6. Optional: check the session file in Terminal:

   ```bash
   ~/Projects/taw-cos-m1/bin/cos history --session default --json | python3 -m json.tool | head -30
   ```

### 7.3 Pin, minimize, close
1. Click the **pin** button in the header. It turns blue.
2. Click into another app. Chief stays on top of it.
3. Click **pin** again. Chief can now go behind other windows.
4. Click the yellow **minimize** button. Chief goes to the Dock. Press **⌃⌥C**, and Chief comes back.
5. Click the red **close** button. Chief hides but keeps running: the menu bar ring is still there.
   Press **⌃⌥C** to bring it back.
6. Quit Chief and open it again. The window keeps its size, position, and pin state.

### 7.4 Daily Brief
1. Click the **Brief** button (the last header button).
   - Expected: a **Daily Brief · not saved** card with the brief lines.
2. **Menu bar ring → Daily Brief** does the same thing and brings Chief to the front.
3. Quit and reopen Chief. The brief card is gone, because briefs are not saved into the session.

### 7.5 Stop and Resume
1. Click **Stop** (bottom left).
   - Expected: the dot turns red (**Stopped**), and the button now says **Resume**.
2. Ask anything.
   - Expected: **"Chief is stopped. Click Resume to continue."** Your question goes back into the input.
3. Open the **menu bar ring** menu. It shows **Resume Chief**.
4. Click **Resume**. The dot turns green.
5. From Terminal: run `~/Projects/taw-cos-m1/bin/cos stop`. Within 30 seconds Chief's dot turns
   red. Then run `~/Projects/taw-cos-m1/bin/cos resume`.

### 7.6 Model unavailable
1. Quit Ollama: **menu bar llama icon → Quit Ollama**.
2. Within 30 seconds, the dot turns gray and says **Local model unavailable**.
3. Ask `Give me one tip for a calm classroom transition`.
   - Expected: **"Chief is running, but the local model isn't available. Open Ollama and try again."**
4. Ask `what time is it`. It still works through the fast path, which uses no model.
5. Open Ollama again. Within 30 seconds the dot is green.

### 7.7 Screen protection (do every part)

The shield in the header shows whether protection is on. A filled shield with a check means on.
Every launch starts with protection on.

**A. Screenshot**
1. With the shield on, press **⌘⇧4**, then **Space**, and click the Chief window.
   - Expected: the saved screenshot doesn't show Chief's content. It is blank or transparent, or
     Chief can't be selected.
2. Click the shield to turn protection off and repeat. Chief's content now shows in the screenshot.
3. Click the shield to turn protection back on.
4. Also try **⌘⇧3** (full screen). Chief's area should be blank with protection on.

**B. QuickTime screen recording**
1. Open **QuickTime Player → File → New Screen Recording**, record the whole screen for about
   10 seconds while Chief is visible, then stop.
2. Play the recording. Chief's window should be blank or missing.

**C. AirPlay mirroring to a display**
1. **Control Center → Screen Mirroring →** choose your Apple TV or AirPlay display, and choose
   **Mirror Built-in Display**.
2. Look at the TV or display. Chief's window should be blank or missing there while it is
   visible on the Mac.
3. Stop mirroring.

**D. Menu bar toggle**: **menu bar ring → Screen protection: on** toggles it, and the header
shield updates to match.

**Important limits (read before teaching with it):**
- Content protection asks macOS to keep the window out of screen capture. Some capture paths
  may not honor it, especially newer ScreenCaptureKit-based apps, so the checks above are the
  proof. Test with the exact tools you use: Zoom, Meet, Teams, and so on.
- A **wired HDMI or USB-C projector in mirror mode** shows the screen directly, not through
  capture, so Chief can **be visible on it**. Follow **Classroom projector** at the top of this
  section, and run check 7.8.

### 7.8 Mirrored display (wired projector or monitor)

Use a projector, TV, or spare monitor connected by HDMI or USB-C. Don't do this in front of
students.

1. With Chief visible and the shield on, connect the display.
2. Open **System Settings → Displays**, select the external display, and set **Use as:** to
   **Mirror for Built-in Display** (wording varies by macOS version).
3. Look at the external display. Write down whether Chief's window shows there.
   - Expected for M1.5A: it may show. Screen protection doesn't cover hardware mirroring.
4. Click Chief, then press **⌃⌥C** (or **Escape**). Chief disappears from both screens.
5. Change **Use as:** to **Extended display**. Drag a Finder window onto the external display to
   confirm it is extended. Press **⌃⌥C**: Chief should appear only on the built-in screen. If it
   opens on the external display, drag it back to the built-in screen. Chief remembers that position.
6. Disconnect the display, and record what you saw in step 3 for the next review.

---

## 8. Quit and clean up

- **Quit:** press **⌘Q** in Chief, or use **menu bar ring → Quit Chief**.
- Chief doesn't start at login in M1.5A. That comes in M1.5B.
- Window geometry is saved in `~/Library/Application Support/Chief/window-state.json`.
  Conversations are saved by `cos` in `~/Library/Application Support/ChiefOfStaff/sessions/`.
- Raycast **Ask Chief** and **Daily Brief** still work as before.
