import { Detail } from "@raycast/api";
import type { ConnectionSnapshot } from "./lib/types";
import { connectionLabel } from "./lib/cosd-client";

export function DisconnectedDetail({ snap }: { snap: ConnectionSnapshot }) {
  const md = `## cosd unavailable

**State:** ${connectionLabel(snap.state)}

${snap.detail ?? ""}

### Recovery
1. Start the daemon: \`bin/cosd start\`
2. If auth fails: \`bin/cosd rotate-token\` then restart cosd
3. Open **Chief.app** → Settings → Runtime for lifecycle controls

No fallback assistant runtime is started from Raycast.`;
  return <Detail markdown={md} />;
}
