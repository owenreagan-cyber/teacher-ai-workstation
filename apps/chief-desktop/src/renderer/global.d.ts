import type { ChiefBridge } from "../shared/types";

declare global {
  interface Window {
    chief: ChiefBridge;
  }
}
