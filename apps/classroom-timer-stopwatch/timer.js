/**
 * Classroom Timer & Stopwatch — local-only runtime prototype.
 * Owen Level 3 approved. No storage, network, audio, or animation APIs.
 */
(function () {
  "use strict";

  /** @type {ReadonlyArray<{label: string, seconds: number, mode: string}>} */
  var PRESETS = [
    { label: "1 minute", seconds: 60, mode: "countdown" },
    { label: "3 minutes", seconds: 180, mode: "countdown" },
    { label: "5 minutes", seconds: 300, mode: "countdown" },
    { label: "10 minutes", seconds: 600, mode: "countdown" },
    { label: "Warmup", seconds: 180, mode: "countdown" },
    { label: "Transition", seconds: 120, mode: "countdown" },
    { label: "Exit ticket", seconds: 120, mode: "countdown" },
  ];

  var DEFAULT_COUNTDOWN_SECONDS = 180;
  var mode = "countdown";
  var running = false;
  var intervalId = null;
  var countdownRemaining = DEFAULT_COUNTDOWN_SECONDS;
  var stopwatchElapsed = 0;
  var tickOrigin = 0;
  var tickBase = 0;
  var announceToken = 0;

  var modeCountdownBtn = document.getElementById("mode-countdown");
  var modeStopwatchBtn = document.getElementById("mode-stopwatch");
  var modeLabel = document.getElementById("mode-label");
  var timeDisplay = document.getElementById("time-display");
  var statusLabel = document.getElementById("status-label");
  var srAnnouncer = document.getElementById("sr-announcer");
  var startBtn = document.getElementById("btn-start");
  var pauseBtn = document.getElementById("btn-pause");
  var resetBtn = document.getElementById("btn-reset");
  var presetsContainer = document.getElementById("presets");

  function parseDurationSeconds(totalSeconds) {
    return Math.max(0, Math.floor(totalSeconds));
  }

  function formatTime(totalSeconds) {
    var s = parseDurationSeconds(totalSeconds);
    var hours = Math.floor(s / 3600);
    var minutes = Math.floor((s % 3600) / 60);
    var seconds = s % 60;
    if (hours > 0) {
      return (
        String(hours) +
        ":" +
        String(minutes).padStart(2, "0") +
        ":" +
        String(seconds).padStart(2, "0")
      );
    }
    return String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
  }

  /** Clears any active interval; safe to call repeatedly. */
  function clearTimerInterval() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  function announceStatus(message) {
    if (!srAnnouncer || !message) {
      return;
    }
    announceToken += 1;
    var token = announceToken;
    srAnnouncer.textContent = "";
    window.setTimeout(function () {
      if (token === announceToken) {
        srAnnouncer.textContent = message;
      }
    }, 30);
  }

  function statusText() {
    if (running) {
      return "Running";
    }
    if (mode === "countdown" && countdownRemaining === 0) {
      return "Complete";
    }
    if (currentValue() === 0 && mode === "stopwatch") {
      return "Ready";
    }
    if (mode === "countdown" && countdownRemaining === DEFAULT_COUNTDOWN_SECONDS) {
      return "Ready";
    }
    return "Paused";
  }

  function currentValue() {
    return mode === "countdown" ? countdownRemaining : stopwatchElapsed;
  }

  function syncControlState() {
    var status = statusText();
    statusLabel.textContent = status;
    statusLabel.setAttribute("data-status", status.toLowerCase());
    startBtn.disabled = running;
    pauseBtn.disabled = !running;
    startBtn.setAttribute("aria-pressed", running ? "true" : "false");
    pauseBtn.setAttribute("aria-pressed", running ? "true" : "false");
    timeDisplay.setAttribute("aria-label", "Time display " + formatTime(currentValue()));
    statusLabel.setAttribute("aria-label", "Timer status " + status);
  }

  function render() {
    timeDisplay.textContent = formatTime(currentValue());
    modeLabel.textContent = mode === "countdown" ? "Countdown" : "Stopwatch";
    modeCountdownBtn.setAttribute("aria-pressed", mode === "countdown" ? "true" : "false");
    modeStopwatchBtn.setAttribute("aria-pressed", mode === "stopwatch" ? "true" : "false");
    syncControlState();
  }

  function tick() {
    var now = Date.now();
    var deltaMs = now - tickOrigin;
    var deltaSec = Math.floor(deltaMs / 1000);
    if (mode === "countdown") {
      countdownRemaining = Math.max(0, tickBase - deltaSec);
      if (countdownRemaining === 0) {
        pause();
        statusLabel.textContent = "Complete";
        announceStatus("Countdown complete");
        syncControlState();
        return;
      }
    } else {
      stopwatchElapsed = tickBase + deltaSec;
    }
    render();
  }

  function startInterval() {
    if (running) {
      return;
    }
    clearTimerInterval();
    tickOrigin = Date.now();
    tickBase = currentValue();
    intervalId = setInterval(tick, 250);
    running = true;
    announceStatus((mode === "countdown" ? "Countdown" : "Stopwatch") + " started");
    render();
  }

  function start() {
    if (running) {
      return;
    }
    if (mode === "countdown" && countdownRemaining <= 0) {
      countdownRemaining = DEFAULT_COUNTDOWN_SECONDS;
    }
    startInterval();
  }

  function pause() {
    if (!running) {
      return;
    }
    tick();
    clearTimerInterval();
    running = false;
    announceStatus("Timer paused");
    render();
  }

  function reset() {
    pause();
    if (mode === "countdown") {
      countdownRemaining = DEFAULT_COUNTDOWN_SECONDS;
    } else {
      stopwatchElapsed = 0;
    }
    announceStatus("Timer reset");
    render();
  }

  function setMode(nextMode) {
    if (mode === nextMode) {
      return;
    }
    pause();
    mode = nextMode;
    if (mode === "countdown") {
      countdownRemaining = DEFAULT_COUNTDOWN_SECONDS;
    } else {
      stopwatchElapsed = 0;
    }
    announceStatus("Mode switched to " + (mode === "countdown" ? "countdown" : "stopwatch"));
    render();
  }

  function applyPreset(index) {
    if (index < 0 || index >= PRESETS.length) {
      return;
    }
    var preset = PRESETS[index];
    pause();
    mode = "countdown";
    countdownRemaining = parseDurationSeconds(preset.seconds);
    announceStatus("Preset applied: " + preset.label + ", " + formatTime(preset.seconds));
    render();
  }

  function isInteractiveTarget(target) {
    if (!target || !target.tagName) {
      return false;
    }
    var tag = target.tagName;
    return tag === "BUTTON" || tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA";
  }

  function buildPresets() {
    PRESETS.forEach(function (preset, index) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = preset.label;
      btn.setAttribute("aria-label", "Preset " + preset.label + ", press " + String(index + 1));
      btn.dataset.presetIndex = String(index);
      btn.addEventListener("click", function () {
        applyPreset(index);
      });
      presetsContainer.appendChild(btn);
    });
  }

  modeCountdownBtn.addEventListener("click", function () {
    setMode("countdown");
  });
  modeStopwatchBtn.addEventListener("click", function () {
    setMode("stopwatch");
  });
  startBtn.addEventListener("click", start);
  pauseBtn.addEventListener("click", pause);
  resetBtn.addEventListener("click", reset);

  document.addEventListener("keydown", function (event) {
    if (event.repeat) {
      return;
    }
    if (isInteractiveTarget(event.target) && (event.key === " " || event.key === "Enter")) {
      return;
    }
    if (event.key === " " || event.code === "Space") {
      event.preventDefault();
      if (running) {
        pause();
      } else {
        start();
      }
      return;
    }
    if (event.key === "r" || event.key === "R") {
      if (isInteractiveTarget(event.target)) {
        return;
      }
      event.preventDefault();
      reset();
      return;
    }
    var digit = parseInt(event.key, 10);
    if (digit >= 1 && digit <= PRESETS.length && !isInteractiveTarget(event.target)) {
      event.preventDefault();
      applyPreset(digit - 1);
    }
  });

  buildPresets();
  render();

  /** Test exports — not used at runtime in browser; for static logic tests only. */
  if (typeof globalThis.__TIMER_TEST_EXPORTS__ !== "undefined") {
    globalThis.__TIMER_TEST_EXPORTS__ = {
      formatTime: formatTime,
      parseDurationSeconds: parseDurationSeconds,
      PRESETS: PRESETS,
      announceStatus: announceStatus,
      statusText: statusText,
    };
  }
})();
