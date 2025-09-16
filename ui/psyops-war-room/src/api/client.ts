import { z } from 'zod';
import type { ActionDefinition, ActionExecutePayload, ActionExecuteResponse } from '@/types/domain';

// Environment flags
const env = import.meta.env as Record<string, string | undefined>;
const API_BASE = env.VITE_API_BASE;
const USE_MOCK = env.VITE_MOCK === 'true' || !API_BASE;

// Standard error shape
export interface ApiErrorShape {
  ok: false;
  status: number;
  code?: string;
  message: string;
  retryable: boolean;
  requestId?: string;
}

export type ApiResult<T> = { ok: true; data: T } | ApiErrorShape;

// Generic fetch wrapper with timeout + basic retry (GET only)
async function http<T>(
  path: string,
  opts: RequestInit & { schema?: z.ZodTypeAny; retries?: number } = {}
): Promise<ApiResult<T>> {
  if (USE_MOCK) {
    return mockRoute<T>(path, opts.schema);
  }
  const { schema, retries = 2, ...rest } = opts;
  const url = `${API_BASE}${path}`;
  let attempt = 0;
  while (true) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10_000);
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json', ...(rest.headers || {}) },
        signal: controller.signal,
        ...rest
      });
      clearTimeout(timer);
      if (!res.ok) {
        const msg = await safeText(res);
        return {
          ok: false,
            status: res.status,
            code: 'HTTP_ERROR',
            message: msg || `Request failed (${res.status})`,
            retryable: res.status >= 500,
            requestId: res.headers.get('x-request-id') || undefined
        };
      }
      const json = (await res.json()) as unknown;
      if (schema) {
        const parsed = schema.safeParse(json);
        if (!parsed.success) {
          return {
            ok: false,
            status: 200,
            code: 'SCHEMA_MISMATCH',
            message: parsed.error.issues.map(i => i.message).join('; '),
            retryable: false
          };
        }
        return { ok: true, data: parsed.data as T };
      }
      return { ok: true, data: json as T };
    } catch (err: unknown) {
      const isAbort = (e: unknown): e is { name: string } =>
        typeof e === 'object' && e !== null && 'name' in e && (e as { name: string }).name === 'AbortError';
      if (isAbort(err)) {
        return { ok: false, status: 0, code: 'TIMEOUT', message: 'Request timed out', retryable: true };
      }
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, 250 * 2 ** attempt));
        attempt++;
        continue;
      }
      const msg = (err as Error)?.message || 'Network error';
      return { ok: false, status: 0, code: 'NETWORK', message: msg, retryable: true };
    }
  }
}

// Schemas
export const EndpointSummarySchema = z.object({
  id: z.string(),
  hostname: z.string(),
  os: z.string(),
  status: z.enum(['online', 'offline', 'degraded']),
  lastSeen: z.string()
});
export const EndpointListSchema = z.array(EndpointSummarySchema);

export const HealthGaugeSchema = z.object({
  overall: z.number().min(0).max(100),
  lastUpdated: z.string(),
  totals: z.object({ online: z.number(), offline: z.number(), degraded: z.number() })
});

// Public API wrappers (endpoints & health)
export function fetchEndpoints() {
  return http<z.infer<typeof EndpointListSchema>>('/api/endpoints', { schema: EndpointListSchema });
}

export function fetchHealth() {
  return http<z.infer<typeof HealthGaugeSchema>>('/health/latest.json', { schema: HealthGaugeSchema });
}

// Actions API (mock friendly for now)
export function listActions() {
  return http<ActionDefinition[]>('/api/actions');
}

export function executeAction(payload: ActionExecutePayload) {
  return http<ActionExecuteResponse>('/api/actions/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' }
  });
}

// Mock routes
function mockRoute<T>(path: string, schema?: z.ZodTypeAny): ApiResult<T> {
  if (path.startsWith('/api/endpoints')) {
    const data = [
      { id: 'e-1', hostname: 'alpha-node', os: 'Windows 11', status: 'online', lastSeen: new Date().toISOString() },
      { id: 'e-2', hostname: 'beta-core', os: 'Ubuntu 24.04', status: 'degraded', lastSeen: new Date(Date.now() - 60_000).toISOString() },
      { id: 'e-3', hostname: 'gamma-edge', os: 'macOS 14', status: 'offline', lastSeen: new Date(Date.now() - 3600_000).toISOString() }
    ];
    return successSchema<T>(data, schema);
  }
  if (path === '/health/latest.json') {
    const data = {
      overall: 82,
      lastUpdated: new Date().toISOString(),
      totals: { online: 10, offline: 2, degraded: 1 }
    };
    return successSchema<T>(data, schema);
  }
  if (path.startsWith('/api/actions')) {
    if (path === '/api/actions') {
      return successSchema<T>([
        { id: 'enable_nla', name: 'Enable NLA' },
        { id: 'enforce_firewall', name: 'Enforce Firewall' }
      ]);
    }
    if (path === '/api/actions/execute') {
      return successSchema<T>({ id: 'act_' + Math.random().toString(36).slice(2, 10) });
    }
  }
  return { ok: false, status: 404, code: 'MOCK_NOT_FOUND', message: `No mock for ${path}`, retryable: false };
}

function successSchema<T>(data: unknown, schema?: z.ZodTypeAny): ApiResult<T> {
  if (schema) {
    const parsed = schema.safeParse(data);
    if (!parsed.success) {
      return {
        ok: false,
        status: 200,
        code: 'SCHEMA_MISMATCH',
        message: parsed.error.issues.map(i => i.message).join('; '),
        retryable: false
      };
    }
    return { ok: true, data: parsed.data as T };
  }
  return { ok: true, data: data as T };
}

async function safeText(res: Response) {
  try { return await res.text(); } catch { return ''; }
}
