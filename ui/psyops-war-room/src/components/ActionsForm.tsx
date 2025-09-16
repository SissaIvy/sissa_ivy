import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { listActions, executeAction } from '@/api/client';
import type { ActionDefinition, ActionExecutePayload } from '@/types/domain';
import ActionTaskPanel from '@/components/ActionTaskPanel';

export default function ActionsForm() {
  const { data: actions } = useQuery({ queryKey: ['actions'], queryFn: listActions });
  const [action, setAction] = useState('');
  const [scope, setScope] = useState("host in ['e-1','e-2']");
  const [paramsText, setParamsText] = useState('{"msg": "hello"}');
  const [paramError, setParamError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | undefined>();

  function parseParams(): Record<string, unknown> | undefined {
    if (!paramsText.trim()) return undefined;
    try {
      const obj = JSON.parse(paramsText);
      if (obj && typeof obj === 'object') return obj as Record<string, unknown>;
      setParamError('Params must be a JSON object.');
      return undefined;
    } catch {
      setParamError('Invalid JSON');
      return undefined;
    }
  }

  const mut = useMutation({
    mutationFn: async () => {
      setParamError(null);
      const parsed = parseParams();
      const payload: ActionExecutePayload = { action, scope, params: parsed };
      return executeAction(payload);
    },
    onSuccess: res => {
      if (res.ok && res.data.id) setTaskId(res.data.id);
    }
  });

  return (
    <section className="card" style={{ maxWidth: 640 }}>
      <h2 style={{ fontSize: 16, marginTop: 0 }}>Runbook Actions</h2>
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <label style={{ fontSize: 12 }}>Action
          <select value={action} onChange={e=>setAction(e.target.value)} style={{ marginTop: 4 }}>
            <option value="">Select…</option>
            {(actions?.ok ? actions.data : ([] as ActionDefinition[])).map(a => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: 12 }}>Scope
          <input value={scope} onChange={e=>setScope(e.target.value)} style={{ width: '100%', marginTop: 4 }} />
        </label>
        <label style={{ fontSize: 12 }}>Params (JSON)
          <input
            value={paramsText}
            onChange={e=>setParamsText(e.target.value)}
            style={{ width: '100%', marginTop: 4 }}
            aria-invalid={paramError ? 'true' : 'false'}
          />
        </label>
      </div>
      {paramError && <div style={{ color: 'var(--c-warn)', fontSize: 12, marginTop: 4 }}>{paramError}</div>}
      <div style={{ marginTop: 12 }}>
        <button onClick={()=>mut.mutate()} disabled={!action || mut.isPending} style={{ padding: '6px 12px' }}>
          {mut.isPending ? 'Dispatching…' : 'Execute'}
        </button>
        {mut.isSuccess && <span className="muted" style={{ marginLeft: 8 }}>Queued: {mut.data.ok ? mut.data.data.id : 'ERR'}</span>}
        {mut.isError && <span style={{ marginLeft: 8, color: 'var(--c-danger)' }}>Failed</span>}
      </div>
      <div style={{ marginTop: 16 }}>
        <ActionTaskPanel taskId={taskId} />
      </div>
    </section>
  );
}
