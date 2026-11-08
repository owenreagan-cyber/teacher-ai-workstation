import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

/** Environment passed to real `bin/cos` invocations in CI and locally. */
export function cosEnv(stateDir) {
  return {
    ...process.env,
    COS_STATE_DIR: stateDir,
    COS_FIXTURE_DIR: path.join(REPO, "evals", "fixtures", "default"),
    TZ: "America/New_York",
    PYTHONPATH: REPO,
  };
}

export { REPO };
