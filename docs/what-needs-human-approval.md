# What Needs Human Approval

Some parts of the Teacher AI Workstation can be automated. Other parts must remain human-approved because they involve accounts, identity, money, privacy, secrets, physical devices, or professional judgment.

## Always human-approved

The following must not be completed silently by scripts or agents.

### Apple and device identity

- Apple Account sign-in.
- iCloud sync decisions.
- Find My configuration.
- FileVault recovery key handling.
- Touch ID or biometric enrollment.
- Device recovery settings.

Scripts may open the relevant System Settings page, but Owen must make the decision.

### 1Password and secrets

- 1Password account creation or sign-in.
- 1Password master password handling.
- 1Password Secret Key handling.
- Recovery code storage.
- API key creation.
- API key retrieval.
- Token creation or revocation.
- Passkey setup.

Scripts and agents must not ask for raw secrets.

### Browser and OAuth sign-in

- Sign in with Google.
- GitHub OAuth approvals.
- OpenAI / ChatGPT sign-in.
- Claude / Anthropic sign-in.
- Gemini / Google AI sign-in.
- Figma sign-in.
- Bambu / MakerWorld sign-in.
- Cursor provider sign-in.

Scripts may open a login URL. Owen completes the login.

### Paid services and subscriptions

- Starting a paid subscription.
- Upgrading a plan.
- Adding a payment method.
- Accepting marketplace purchases.
- Buying software, models, filament, services, or cloud credits.

### macOS privacy permissions

macOS privacy permissions require human approval and often cannot be reliably verified from scripts.

Examples:

- Accessibility.
- Full Disk Access.
- Screen Recording.
- Contacts.
- Calendars.
- Files and folders.
- Camera and microphone.
- Automation permissions.

A script may guide Owen to the correct settings pane, but it must not claim full confirmation unless verification is reliable.

### Physical devices and local environment

- Bambu printer pairing.
- Printer QR code scan.
- Ricoh school printer certification.
- Network printer selection.
- Classroom network access.
- iPad/iPhone Focus sync.
- Physical device testing.

### School and student data

Human approval is required before using, moving, summarizing, sharing, exporting, or automating anything involving:

- Student records.
- Parent information.
- Grades.
- Behavior notes.
- Medical information.
- Accommodation information.
- Confidential school documents.

This workstation is not a student data system.

### Commercial and 3D printing decisions

Human approval is required for:

- Commercial product decisions.
- IP/license review.
- Safety-sensitive designs.
- Customer/client requests.
- Bambu Studio print preview approval.
- Any design being treated as ready for sale.

AI-generated 3D designs may be described as slicer-ready pending human verification, not print-ready.

## Assisted is not automatic

Some tasks can be assisted but not completed automatically.

Examples:

- Opening a login page.
- Opening System Settings.
- Showing a checklist.
- Running a read-only status command.
- Opening an app for first-run setup.

The assistant should describe these as assisted or guided, not fully automated.

## Approval labels

Future plans should label tasks as one of:

- Safe to automate.
- Interactive only.
- Human approval required.
- Never automate.
- Later phase.

## Default rule

If a task touches identity, secrets, money, student data, account access, privacy permissions, destructive changes, or commercial approval, ask Owen before acting.