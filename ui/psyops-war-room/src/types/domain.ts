// ---- Health / Probe ----
export interface EndpointSummary {
  id: string;
  hostname: string;
  os: string;
  status: 'online' | 'offline' | 'degraded';
  lastSeen: string;
}

// Existing (could map to health document later)
export type HealthDoc = {
  generated_at?: string;
  health_index?: number;
};

// ---- Actions (PsyOps) ----
export type ActionDefinition = { id: string; name: string };

export type ActionExecutePayload = {
  action: string;
  scope: string; // e.g., "host in ['WS-001','WS-002']"
  params?: Record<string, unknown>;
};

export type ActionExecuteResponse = { id: string };

export type ActionStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELED';
export type ActionEvent = { id: string; status: ActionStatus; ts: string; message?: string };
export type ActionTask = { id: string; startedAt: string; status: ActionStatus; events: ActionEvent[] };

// Legacy invoke request/response (mapped to new forms)
export interface ActionInvokeRequest {
  action: string;
  targetIds: string[];
  params?: Record<string, unknown>;
}
export interface ActionInvokeResponse { taskId: string }
