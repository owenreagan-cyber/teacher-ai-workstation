import { useCallback, useEffect, useState } from "react";

import type { CosdConnectionSnapshot, CosdTask, TaskHistoryEvent, TaskState } from "../shared/cosd";
import { DEV_SCAN_KIND, type DevScanReport } from "../shared/devscan";
import { DevScanPanel, DevScanReportView } from "./DevScan";

const STATES: (TaskState | "")[] = ["", "QUEUED", "RUNNING", "COMPLETED", "FAILED", "BLOCKED", "CANCELLED"];

function stateTone(state: TaskState): string {
  switch (state) {
    case "RUNNING":
    case "CLAIMED":
      return "text-accent";
    case "FAILED":
      return "text-bad";
    case "BLOCKED":
      return "text-warn";
    case "COMPLETED":
      return "text-good";
    default:
      return "text-muted";
  }
}

export function TaskCenter() {
  const [filter, setFilter] = useState<TaskState | "">("");
  const [tasks, setTasks] = useState<CosdTask[]>([]);
  const [selected, setSelected] = useState<CosdTask | null>(null);
  const [history, setHistory] = useState<TaskHistoryEvent[]>([]);
  const [conn, setConn] = useState<CosdConnectionSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [queuePaused, setQueuePaused] = useState<boolean | null>(null);
  const [scanReport, setScanReport] = useState<DevScanReport | null>(null);
  const [scanNote, setScanNote] = useState<string | null>(null);

  const refreshConnection = useCallback(async () => {
    const res = await window.chief.cosdConnection();
    if (res.ok) setConn(res.snapshot);
  }, []);

  const loadTasks = useCallback(async () => {
    setError(null);
    const res = await window.chief.listTasks(filter || undefined);
    if (res.ok) setTasks(res.tasks);
    else setError(res.error);
  }, [filter]);

  const loadQueue = useCallback(async () => {
    const res = await window.chief.queueSnapshot();
    if (res.ok) setQueuePaused(res.queue.paused);
  }, []);

  useEffect(() => {
    void refreshConnection();
    void loadTasks();
    void loadQueue();
    const id = setInterval(() => {
      void loadTasks();
      void loadQueue();
      void refreshConnection();
    }, 20_000);
    const off = window.chief.onEvent((event) => {
      if (event.kind === "cosd-task-event" || event.kind === "cosd-connection") {
        void loadTasks();
        void loadQueue();
        if (event.kind === "cosd-connection") void refreshConnection();
      }
    });
    return () => {
      clearInterval(id);
      off();
    };
  }, [loadTasks, loadQueue, refreshConnection]);

  const loadScanReport = async (task: CosdTask) => {
    setScanReport(null);
    setScanNote(null);
    if (task.kind !== DEV_SCAN_KIND) return;
    const res = await window.chief.devScanReport(task.id);
    if (!res.ok) setScanNote(res.error);
    else if (res.report) setScanReport(res.report);
    else if (res.error) setScanNote(res.error);
  };

  const openTask = async (task: CosdTask) => {
    setSelected(task);
    const res = await window.chief.taskHistory(task.id);
    setHistory(res.ok ? res.events : []);
    await loadScanReport(task);
  };

  // A scan the owner starts from the panel: refresh the list and show its report in the detail pane.
  const showScan = async (taskId: string) => {
    await loadTasks();
    const res = await window.chief.getTask(taskId);
    if (res.ok) await openTask(res.task);
  };

  // Retry on a scan task re-queues it and runs it again: the owner's click is the explicit start.
  const retryOrRunScan = async (task: CosdTask) => {
    if (task.kind !== DEV_SCAN_KIND) {
      await window.chief.retryTask(task.id);
      await loadTasks();
      return;
    }
    if (task.state !== "QUEUED") {
      const res = await window.chief.retryTask(task.id);
      if (!res.ok) {
        setError(res.error);
        return;
      }
    }
    const run = await window.chief.devScanExecute(task.id);
    if (!run.ok) setError(run.error);
    await showScan(task.id);
  };

  const reconnect = async () => {
    const res = await window.chief.cosdReconnect();
    if (res.ok) setConn(res.snapshot);
    await loadTasks();
  };

  const createDiagnostic = async () => {
    const key = crypto.randomUUID();
    const res = await window.chief.createTask("Desktop check-in", "diagnostic", key);
    if (!res.ok) setError(res.error);
    else await loadTasks();
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-[12px] text-muted">
        <span>
          Runtime: {conn?.execution_mode === "daemon" ? "cosd" : "standalone"}
          {conn?.state ? ` · ${conn.state}` : ""}
        </span>
        {queuePaused !== null && <span>Queue {queuePaused ? "paused" : "active"}</span>}
        <button type="button" onClick={() => void reconnect()} className="text-accent hover:underline">
          Retry connection
        </button>
        {conn?.detail && <span className="text-warn">{conn.detail}</span>}
      </div>
      {error && <p className="text-[13px] text-bad">{error}</p>}
      <DevScanPanel bridge={window.chief} onRan={(res) => void showScan(res.task_id)} />
      <div className="flex flex-wrap gap-2">
        {STATES.map((s) => (
          <button
            key={s || "all"}
            type="button"
            onClick={() => setFilter(s)}
            className={`rounded-md border px-2 py-1 text-[12px] ${filter === s ? "border-accent text-accent" : "border-line text-muted"}`}
          >
            {s || "All"}
          </button>
        ))}
        <button type="button" onClick={() => void createDiagnostic()} className="ml-auto rounded-md bg-accent px-2 py-1 text-[12px] text-on-accent">
          New diagnostic task
        </button>
      </div>
      <ul className="divide-y divide-line rounded-xl border border-line bg-surface">
        {tasks.length === 0 ? (
          <li className="p-4 text-[13px] text-muted">No tasks {conn?.state !== "CONNECTED" ? "(start cosd with bin/cosd start)" : ""}</li>
        ) : (
          tasks.map((t) => (
            <li key={t.id}>
              <button type="button" onClick={() => void openTask(t)} className="flex w-full items-start gap-3 p-3 text-left hover:bg-bg">
                <span className={`shrink-0 font-mono text-[12px] ${stateTone(t.state)}`}>{t.state}</span>
                <span className="min-w-0 flex-1">
                  <div className="text-[13px] font-medium">{t.title}</div>
                  <div className="text-[12px] text-muted">
                    {t.kind}
                    {t.attempt_count !== null ? ` · attempts ${t.attempt_count}` : ""}
                    {t.blocked_reason ? ` · ${t.blocked_reason}` : ""}
                  </div>
                </span>
              </button>
            </li>
          ))
        )}
      </ul>
      {selected && (
        <section className="rounded-xl border border-line bg-surface p-4">
          <div className="mb-2 flex items-center gap-2">
            <h2 className="text-[14px] font-semibold">{selected.title}</h2>
            <span className="font-mono text-[12px] text-muted">{selected.id.slice(0, 8)}…</span>
          </div>
          <p className="text-[12px] text-muted">
            Updated {selected.updated_at}
            {selected.last_error ? ` · ${selected.last_error}` : ""}
          </p>
          <div className="mt-3 flex gap-2">
            {["QUEUED", "RUNNING", "BLOCKED"].includes(selected.state) && (
              <button type="button" onClick={() => void window.chief.cancelTask(selected.id).then(() => loadTasks())} className="rounded border border-line px-2 py-1 text-[12px]">
                Cancel
              </button>
            )}
            {(["FAILED", "BLOCKED"].includes(selected.state) || (selected.kind === DEV_SCAN_KIND && selected.state === "QUEUED")) && (
              <button type="button" onClick={() => void retryOrRunScan(selected)} className="rounded border border-line px-2 py-1 text-[12px]">
                {selected.kind === DEV_SCAN_KIND ? (selected.state === "QUEUED" ? "Run scan" : "Retry scan") : "Retry"}
              </button>
            )}
          </div>
          {scanReport && (
            <div className="mt-3 border-t border-line pt-3">
              <DevScanReportView report={scanReport} />
            </div>
          )}
          {!scanReport && scanNote && <p className="mt-3 text-[13px] text-bad">{scanNote}</p>}
          <ul className="mt-3 max-h-48 space-y-1 overflow-y-auto text-[12px] text-muted">
            {history.map((ev, i) => (
              <li key={`${ev.ts}-${i}`}>
                <span className="font-mono">{ev.ts}</span> — {ev.event}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
