export default function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="muted" style={{ padding: 8 }}>
      {label}
    </div>
  );
}
