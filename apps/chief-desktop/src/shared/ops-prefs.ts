export type OpsPrefs = {
  notifyTaskCompleted: boolean;
  notifyTaskFailed: boolean;
  notifyTaskBlocked: boolean;
  notifyRecovery: boolean;
  notifyDaemonConnection: boolean;
  streamingAsk: boolean;
  progressViaEvents: boolean;
};

export const DEFAULT_OPS_PREFS: OpsPrefs = {
  notifyTaskCompleted: true,
  notifyTaskFailed: true,
  notifyTaskBlocked: true,
  notifyRecovery: true,
  notifyDaemonConnection: true,
  streamingAsk: true,
  progressViaEvents: true,
};
