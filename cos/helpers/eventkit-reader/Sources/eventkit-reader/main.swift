// eventkit-reader: read-only EventKit access that prints JSON on stdout.
//
// Runs only as ChiefOfStaffEventKitReader.app launched through LaunchServices
// (`open -W -n -g -j --stdout F --stderr F App.app --args ...`), so the app is its
// own responsible process and macOS attributes the Calendar/Reminders grant to this
// bundle identity, not to Terminal or Raycast. EventKit commands refuse to run when
// the process is not its own responsible process or not inside the expected bundle.
//
//   events --days N                  events from start of today for N days (1-14)
//   reminders --due-within-days N    incomplete reminders due by end of day N (incl. overdue)
//   status                           authorization status only; never prompts
//   identity                         bundle/process attribution facts; no EventKit use
//   --version
//
// Output: {"status": "ok", ...} with exit 0, or {"status": "denied" | "restricted" |
// "not_determined" | "write_only" | "wrong_launch" | "error", "message": ...} with exit 3
// (2 for usage). Only title, times, all-day flag, and calendar/list name are emitted.
// Notes, attendees, locations, and URLs are never read. There is no command that
// creates, edits, or deletes anything: macOS offers no read-only EventKit tier for
// reading events, so read-only behavior is enforced here, in code.
// COS_EVENTKIT_NO_PROMPT=1 reports not_determined instead of prompting.

import Darwin
import EventKit
import Foundation

let version = "0.2.0"
let expectedBundleID = "local.chief-of-staff.eventkit-reader"
/// Created lazily on first EventKit use, so identity/--version never touch EventKit.
enum EK { static let store = EKEventStore() }
let iso: ISO8601DateFormatter = {
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime]
    f.timeZone = .current
    return f
}()

func emit(_ object: [String: Any], code: Int32) -> Never {
    if let data = try? JSONSerialization.data(withJSONObject: object, options: [.sortedKeys]) {
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data("\n".utf8))
    }
    exit(code)
}

func fail(_ status: String, _ message: String, code: Int32 = 3) -> Never {
    emit(["status": status, "message": message], code: code)
}

func intOption(_ name: String, in args: [String], default value: Int, range: ClosedRange<Int>) -> Int {
    guard let i = args.firstIndex(of: name) else { return value }
    guard i + 1 < args.count, let n = Int(args[i + 1]), range.contains(n) else {
        fail("error", "\(name) needs an integer in \(range)", code: 2)
    }
    return n
}

func statusName(_ s: EKAuthorizationStatus) -> String {
    switch s {
    case .fullAccess: return "ok"
    case .writeOnly: return "write_only"
    case .denied: return "denied"
    case .restricted: return "restricted"
    case .notDetermined: return "not_determined"
    @unknown default: return "unknown"
    }
}

func ensureAccess(_ type: EKEntityType) {
    let current = statusName(EKEventStore.authorizationStatus(for: type))
    if current == "ok" { return }
    let noPrompt = ProcessInfo.processInfo.environment["COS_EVENTKIT_NO_PROMPT"] == "1"
    if current != "not_determined" || noPrompt {
        fail(current, "\(type == .event ? "Calendar" : "Reminders") full access not granted")
    }
    let done = DispatchSemaphore(value: 0)
    var granted = false
    let handler: EKEventStoreRequestAccessCompletionHandler = { ok, _ in
        granted = ok
        done.signal()
    }
    if type == .event {
        EK.store.requestFullAccessToEvents(completion: handler)
    } else {
        EK.store.requestFullAccessToReminders(completion: handler)
    }
    done.wait()
    if !granted {
        fail("denied", "\(type == .event ? "Calendar" : "Reminders") access was not granted")
    }
}

typealias ResponsibleFn = @convention(c) (pid_t) -> pid_t

/// The pid macOS holds responsible for this process (TCC attribution), if the
/// responsibility API is available. RTLD_DEFAULT is (void *)-2 on Darwin.
func responsiblePID() -> pid_t? {
    guard let sym = dlsym(UnsafeMutableRawPointer(bitPattern: -2),
                          "responsibility_get_pid_responsible_for_pid") else { return nil }
    let fn = unsafeBitCast(sym, to: ResponsibleFn.self)
    return fn(getpid())
}

func identityFacts() -> [String: Any] {
    let responsible = responsiblePID()
    return [
        "bundle_id": Bundle.main.bundleIdentifier ?? NSNull(),
        "bundle_path": Bundle.main.bundlePath,
        "pid": Int(getpid()),
        "ppid": Int(getppid()),
        "responsible_pid": responsible.map { Int($0) } ?? NSNull(),
        "self_responsible": responsible.map { $0 == getpid() } ?? NSNull(),
        "no_prompt": ProcessInfo.processInfo.environment["COS_EVENTKIT_NO_PROMPT"] == "1",
    ]
}

/// EventKit attribution guard: only the launched app bundle may touch EventKit.
func requireOwnIdentity() {
    guard Bundle.main.bundleIdentifier == expectedBundleID, Bundle.main.bundlePath.hasSuffix(".app") else {
        fail("wrong_launch", "EventKit commands run only inside ChiefOfStaffEventKitReader.app")
    }
    guard let responsible = responsiblePID() else {
        fail("wrong_launch", "cannot confirm TCC attribution (responsibility API unavailable)")
    }
    guard responsible == getpid() else {
        fail("wrong_launch", "launched as a child of pid \(responsible); use LaunchServices (open) so this app owns the permission")
    }
}

func events(days: Int) -> Never {
    ensureAccess(.event)
    let cal = Calendar.current
    let start = cal.startOfDay(for: Date())
    guard let end = cal.date(byAdding: .day, value: days, to: start) else { fail("error", "date math failed") }
    let predicate = EK.store.predicateForEvents(withStart: start, end: end, calendars: nil)
    let items: [[String: Any]] = EK.store.events(matching: predicate).map { ev in
        [
            "title": ev.title ?? "",
            "start": iso.string(from: ev.startDate),
            "end": iso.string(from: ev.endDate),
            "all_day": ev.isAllDay,
            "calendar": ev.calendar?.title ?? "",
        ]
    }
    emit(["status": "ok", "events": items], code: 0)
}

func reminders(dueWithinDays days: Int) -> Never {
    ensureAccess(.reminder)
    let cal = Calendar.current
    let today = cal.startOfDay(for: Date())
    guard let end = cal.date(byAdding: .day, value: days, to: today) else { fail("error", "date math failed") }
    let predicate = EK.store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: end, calendars: nil)
    let done = DispatchSemaphore(value: 0)
    var items: [[String: Any]] = []
    EK.store.fetchReminders(matching: predicate) { found in
        for r in found ?? [] {
            guard let comps = r.dueDateComponents, let due = cal.date(from: comps) else { continue }
            items.append([
                "title": r.title ?? "",
                "due": iso.string(from: due),
                "date_only": comps.hour == nil,
                "list": r.calendar?.title ?? "",
            ])
        }
        done.signal()
    }
    done.wait()
    emit(["status": "ok", "reminders": items], code: 0)
}

let args = Array(CommandLine.arguments.dropFirst())
switch args.first {
case "events":
    requireOwnIdentity()
    events(days: intOption("--days", in: args, default: 1, range: 1...14))
case "reminders":
    requireOwnIdentity()
    reminders(dueWithinDays: intOption("--due-within-days", in: args, default: 1, range: 1...14))
case "status":
    requireOwnIdentity()
    emit(["status": "ok",
          "calendar": statusName(EKEventStore.authorizationStatus(for: .event)),
          "reminders": statusName(EKEventStore.authorizationStatus(for: .reminder))], code: 0)
case "identity":
    emit(["status": "ok"].merging(identityFacts()) { a, _ in a }, code: 0)
case "--version":
    emit(["status": "ok", "version": version], code: 0)
default:
    fail("error", "usage: eventkit-reader events --days N | reminders --due-within-days N | status | identity | --version", code: 2)
}
