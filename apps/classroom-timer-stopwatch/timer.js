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

  var mode = "countdown";
  var running = false;
  var intervalId = null;
  var countdownRemaining = 0;
  var stopwatchElapsed = 0;
  var tickOrigin = 0;
  var tickBase = 0;

  var modeCountdownBtn = document.getElementById("mode-countdown");
  var modeStopwatchBtn = document.getElementById("mode-stopwatch");
  var modeLabel = document.getElementById("mode-label");
  var timeDisplay = document.getElementById("time-display");
  var statusLabel = document.getElementById("status-label");
  var startBtn = document.getElementById("btn-start");
  var pauseBtn = document.getElementById("btn-pause");
  var resetBtn = document.getElementById("btn-reset");
  var presetsContainer = document.getElementById("presets");

  function parseDurationSeconds(totalSeconds) {
    var s = Math.max(0, Math.floor(totalSeconds));
    return s;
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

  function clearTimerInterval() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  function currentValue() {
    return mode === "countdown" ? countdownRemaining : stopwatchElapsed;
  }

  function render() {
    timeDisplay.textContent = formatTime(currentValue());
    modeLabel.textContent = mode === "countdown" ? "Countdown" : "Stopwatch";
    modeCountdownBtn.setAttribute("aria-pressed", mode === "countdown" ? "true" : "false");
    modeStopwatchBtn.setAttribute("aria-pressed", mode === "stopwatch" ? "true" : "false");
    statusLabel.textContent = running
      ? "Running"
      : currentValue() === 0 && mode === "countdown"
        ? "Ready"
        : "Paused";
    startBtn.disabled = running;
    pauseBtn.disabled = !running;
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
      }
    } else {
      stopwatchElapsed = tickBase + deltaSec;
    }
    render();
  }

  function startInterval() {
    clearTimerInterval();
    tickOrigin = Date.now();
    tickBase = currentValue();
    intervalId = setInterval(tick, 250);
    running = true;
    render();
  }

  function start() {
    if (running) {
      return;
    }
    if (mode === "countdown" && countdownRemaining <= 0) {
      countdownRemaining = 180;
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
    render();
  }

  function reset() {
    pause();
    if (mode === "countdown") {
      countdownRemaining = 180;
    } else {
      stopwatchElapsed = 0;
    }
    statusLabel.textContent = "Ready";
    render();
  }

  function setMode(nextMode) {
    if (mode === nextMode) {
      return;
    }
    pause();
    mode = nextMode;
    if (mode === "countdown") {
      countdownRemaining = 180;
    } else {
      stopwatchElapsed = 0;
    }
    render();
  }

  function applyPreset(seconds) {
    pause();
    mode = "countdown";
    countdownRemaining = parseDurationSeconds(seconds);
    render();
  }

  function buildPresets() {
    PRESETS.forEach(function (preset) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = preset.label;
      btn.setAttribute("aria-label", "Preset " + preset.label);
      btn.addEventListener("click", function () {
        applyPreset(preset.seconds);
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
    if (event.target && (event.target.tagName === "BUTTON" || event.target.tagName === "INPUT")) {
      if (event.key === " " || event.key === "Enter") {
        return;
      }
    }
    if (event.key === " " || event.code === "Space") {
      event.preventDefault();
      if (running) {
        pause();
      } else {
        start();
      }
    } else if (event.key === "r" || event.key === "R") {
      reset();
    }
  });

  buildPresets();
  countdownRemaining = 180;
  render();

  /** Test exports — not used at runtime in browser; for static logic tests only. */
  if (typeof globalThis.__TIMER_TEST_EXPORTS__ !== "undefined") {
    globalThis.__TIMER_TEST_EXPORTS__ = {
      formatTime: formatTime,
      parseDurationSeconds: parseDurationSeconds,
      PRESETS: PRESETS,
    };
  }
})();
