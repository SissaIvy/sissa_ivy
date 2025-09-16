import { useEffect, useMemo, useRef, useState } from 'react';
import type { ActionEvent, ActionStatus } from '@/types/actions';

type Options = {
  /** Optional: provide when you know the server start time */
  startedAt?: string;
  /** Simulated delay before RUNNING (ms) */
  runDelayMs?: number;
  /** Simulated delay before SUCCEEDED (ms) */
  successDelayMs?: number;
};



/** Mock‑friendly task status: progresses via timeouts (test‑stable). */
export function useActionTask(taskId?: string, opts: Options = {}) {
  const [events, setEvents] = useState<ActionEvent[]>([]);
  const [status, setStatus] = useState<ActionStatus>('PENDING');
  const [done, setDone] = useState(false);
  const startRef = useRef<number | null>(null);

  const startedAtIso = useMemo(() => {
    if (opts.startedAt) return opts.startedAt;
    if (taskId && startRef.current == null) startRef.current = Date.now();
    return startRef.current ? new Date(startRef.current).toISOString() : new Date().toISOString();
  }, [taskId, opts.startedAt]);

  useEffect(() => {
    if (!taskId) {
      setEvents([]);
      setStatus('PENDING');
      setDone(false);
      startRef.current = null;
      return;
    }

    const now = Date.now();
    if (startRef.current == null) startRef.current = now;
    const runDelay = Math.max(0, opts.runDelayMs ?? 400);
    const successDelay = Math.max(runDelay + 1, opts.successDelayMs ?? 2000);

    // Seed with PENDING immediately
    const seed: ActionEvent = {
      id: `${taskId}:0`,
      status: 'PENDING',
      ts: new Date(startRef.current).toISOString(),
      message: 'Task accepted'
    };
    setEvents([seed]);
    setStatus('PENDING');
    setDone(false);

    const tRun = window.setTimeout(() => {
      const ev: ActionEvent = {
        id: `${taskId}:1`,
        status: 'RUNNING',
        ts: new Date((startRef.current ?? now) + runDelay).toISOString(),
        message: 'Executing'
      };
      setEvents(prev => (prev.some(e => e.status === 'RUNNING') ? prev : [...prev, ev]));
      setStatus('RUNNING');
    }, runDelay);

    const tDone = window.setTimeout(() => {
      const ev: ActionEvent = {
        id: `${taskId}:2`,
        status: 'SUCCEEDED',
        ts: new Date((startRef.current ?? now) + successDelay).toISOString(),
        message: 'Completed'
      };
      setEvents(prev => [...prev, ev]);
      setStatus('SUCCEEDED');
      setDone(true);
    }, successDelay);

    return () => {
      window.clearTimeout(tRun);
      window.clearTimeout(tDone);
    };
  }, [taskId, opts.runDelayMs, opts.successDelayMs]);

  return { taskId, startedAt: startedAtIso, events, status, done };
}

export default useActionTask;
