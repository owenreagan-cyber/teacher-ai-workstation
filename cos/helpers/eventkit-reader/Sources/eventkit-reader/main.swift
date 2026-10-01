// eventkit-reader: read-only EventKit access that prints JSON on stdout.
//
//   eventkit-reader events --days N               events from start of today for N days
//   eventkit-reader reminders --due-within-days N incomplete reminders due by end of day N (incl. overdue)
//   eventkit-reader status                        authorization status only; never prompts
//   eventkit-reader --version
//
// Output: {"status": "ok", ...} with exit 0, or {"status": "denied" | "restricted" |
// "not_determined" | "write_only" | "error", "message": ...} with exit 3 (2 for usage).
// Only title, times, all-day flag, and calendar/list name are emitted. Notes, attendees,
// locations, and URLs are never read. Nothing is ever written to EventKit.
// COS_EVENTKIT_NO_PROMPT=1 reports not_determined instead of prompting.

import EventKit
import Foundation

let version = "0.1.0"
let store = EKEventStore()
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
        store.requestFullAccessToEvents(completion: handler)
    } else {
        store.requestFullAccessToReminders(completion: handler)
    }
    done.wait()
    if !granted {
        fail("denied", "\(type == .event ? "Calendar" : "Reminders") access was not granted")
    }
}

func events(days: Int) -> Never {
    ensureAccess(.event)
    let cal = Calendar.current
    let start = cal.startOfDay(for: Date())
    guard let end = cal.date(byAdding: .day, value: days, to: start) else { fail("error", "date math failed") }
    let predicate = store.predicateForEvents(withStart: start, end: end, calendars: nil)
    let items: [[String: Any]] = store.events(matching: predicate).map { ev in
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
    let predicate = store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: end, calendars: nil)
    let done = DispatchSemaphore(value: 0)
    var items: [[String: Any]] = []
    store.fetchReminders(matching: predicate) { found in
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
    events(days: intOption("--days", in: args, default: 1, range: 1...14))
case "reminders":
    reminders(dueWithinDays: intOption("--due-within-days", in: args, default: 1, range: 1...14))
case "status":
    emit(["status": "ok",
          "calendar": statusName(EKEventStore.authorizationStatus(for: .event)),
          "reminders": statusName(EKEventStore.authorizationStatus(for: .reminder))], code: 0)
case "--version":
    emit(["status": "ok", "version": version], code: 0)
default:
    fail("error", "usage: eventkit-reader events --days N | reminders --due-within-days N | status | --version", code: 2)
}
