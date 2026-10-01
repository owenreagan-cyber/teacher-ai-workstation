// Inline SVG icons (no icon library). 16px, currentColor.
type P = { className?: string };
const base = {
  width: 16,
  height: 16,
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round",
  strokeLinejoin: "round",
} as const;

export const ShieldIcon = ({ on, className }: P & { on: boolean }) => (
  <svg {...base} className={className} aria-hidden="true">
    <path
      d="M8 1.75 2.75 3.5v4c0 3.1 2.2 5.6 5.25 6.75 3.05-1.15 5.25-3.65 5.25-6.75v-4L8 1.75Z"
      fill={on ? "currentColor" : "none"}
      fillOpacity={on ? 0.2 : 0}
    />
    {on ? <path d="m5.75 8 1.5 1.5 3-3" /> : <path d="m6 6 4 4M10 6l-4 4" />}
  </svg>
);

export const PinIcon = ({ on, className }: P & { on: boolean }) => (
  <svg {...base} className={className} aria-hidden="true">
    <path d="M6 2.5h4l-.5 4 2 2v1H4.5v-1l2-2L6 2.5Z" fill={on ? "currentColor" : "none"} fillOpacity={on ? 0.35 : 0} />
    <path d="M8 9.5v4" />
  </svg>
);

export const BriefIcon = ({ className }: P) => (
  <svg {...base} className={className} aria-hidden="true">
    <rect x="2.5" y="2.5" width="11" height="11" rx="2" />
    <path d="M5 6h6M5 8.5h6M5 11h3.5" />
  </svg>
);

export const StopIcon = ({ className }: P) => (
  <svg {...base} className={className} aria-hidden="true">
    <rect x="4" y="4" width="8" height="8" rx="1.5" />
  </svg>
);

export const PlayIcon = ({ className }: P) => (
  <svg {...base} className={className} aria-hidden="true">
    <path d="M5 3.5v9l7-4.5-7-4.5Z" />
  </svg>
);

export const ExpandIcon = ({ className }: P) => (
  <svg {...base} className={className} aria-hidden="true">
    <path d="M9.5 2.5h4v4M6.5 13.5h-4v-4M13.5 2.5 9 7M2.5 13.5 7 9" />
  </svg>
);
