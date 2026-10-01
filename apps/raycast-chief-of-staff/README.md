# Chief of Staff — Raycast extension (M1)

Two commands that call the local `cos` CLI. The extension itself makes no network
requests. Every answer comes from a local Ollama model on this Mac.

| Command | Runs | Shows |
|---|---|---|
| **Ask Chief** | `bin/cos ask --json "<question>"` | the answer, notes, tools used, and the model |
| **Daily Brief** | `bin/cos brief --json` | the brief (15 lines at most) |

## Setup (Owen, once)

Prerequisites: Raycast, Node 20+ and npm, `python3.12` (Homebrew), and Ollama running with
`qwen3.6:35b` installed.

1. Install the dependencies. This downloads `@raycast/api`, TypeScript, and type packages from npm:
   ```bash
   cd ~/Projects/teacher-ai-workstation/apps/raycast-chief-of-staff
   npm install
   ```
2. Import the extension into Raycast:
   ```bash
   npm run dev
   ```
   Raycast opens and lists **Chief of Staff** under Extensions. `npm run dev` (`ray develop`)
   keeps running and watches the files. Once Raycast shows the extension, stop it with
   **Ctrl-C**. The extension stays imported.
3. In Raycast, go to **Settings → Extensions → Chief of Staff** and set **Path to bin/cos**
   if the repo is not at `~/Projects/teacher-ai-workstation`.
4. Assign the hotkey: in the same settings pane, select **Ask Chief** → **Hotkey** and press
   the shortcut you want (for example ⌥Space). Optionally give **Daily Brief** one too.

## Use

- Hotkey → type the question in the argument field → Enter. Leave it blank to get a larger
  text box.
- If the kill switch is set (`cos stop`), both commands show the error until you run `cos resume`.

## Notes

- Calendar and Reminders permission is granted on the first live run (see
  `docs/cos-m1-live-checks.md`). macOS attributes the permission to the app that launches
  the helper, so Raycast asks once separately from Terminal.
- The first question after a while may take longer while Ollama loads the model.
