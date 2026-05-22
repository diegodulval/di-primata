import { useEffect, useState } from "react";
import { API_BASE_URL } from "../constants";

type Status = "checking" | "ok" | "unavailable";

export function useApiHealth(): { status: Status; retry: () => void } {
  const [status, setStatus] = useState<Status>("checking");
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      setStatus("checking");
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(5000) });
        if (!cancelled) setStatus(res.ok ? "ok" : "unavailable");
      } catch {
        if (!cancelled) setStatus("unavailable");
      }
    }

    void check();
    return () => {
      cancelled = true;
    };
  }, [tick]);

  return { status, retry: () => setTick((t) => t + 1) };
}
