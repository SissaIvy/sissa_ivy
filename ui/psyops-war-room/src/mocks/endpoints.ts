import { EndpointSummary } from '../types/domain';

export function getMockEndpoints(): EndpointSummary[] {
  return [
    { id: 'e-1', hostname: 'alpha-node', os: 'Windows 11', status: 'online', lastSeen: new Date().toISOString() },
    { id: 'e-2', hostname: 'beta-core', os: 'Ubuntu 24.04', status: 'degraded', lastSeen: new Date(Date.now() - 60_000).toISOString() },
    { id: 'e-3', hostname: 'gamma-edge', os: 'macOS 14', status: 'offline', lastSeen: new Date(Date.now() - 3600_000).toISOString() }
  ];
}
