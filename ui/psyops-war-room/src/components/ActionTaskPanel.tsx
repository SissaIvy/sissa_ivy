import useActionTask from '@/hooks/useActionTask';

export default function ActionTaskPanel({ taskId }: { taskId?: string }) {
  // Default simulated timings: RUNNING ~0.4s, SUCCEEDED ~2.0s
  const { events, status, done, startedAt } = useActionTask(taskId);
  if (!taskId) return null;
  return (
    <section className="card" aria-labelledby="task-status">
      <h3 id="task-status">Action Status</h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span className={`sev ${status.toLowerCase()}`}>{status}</span>
        <span className="muted">Started: {new Date(startedAt).toLocaleString()}</span>
        {done ? <span className="badge">DONE</span> : <span className="badge">IN‑FLIGHT</span>}
      </div>
      <ol style={{ margin: 0, paddingLeft: 18 }}>
        {events.map(ev => (
          <li key={ev.id} style={{ marginBottom: 6 }}>
            <strong>{ev.status}</strong>
            <span className="muted"> — {new Date(ev.ts).toLocaleTimeString()}</span>
            {ev.message ? <span className="muted"> • {ev.message}</span> : null}
          </li>
        ))}
      </ol>
    </section>
  );
}
