import React from 'react';
import { useEndpoints } from '../hooks/useEndpoints';

export const EndpointsOverview: React.FC = () => {
  const { data, isLoading } = useEndpoints();
  if (isLoading) return <div>Loading endpoints...</div>;
  return (
    <div>
      <h2 style={{ fontSize: 16, marginBottom: 8 }}>Endpoints</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ textAlign: 'left' }}>
            <th>Name</th>
            <th>OS</th>
            <th>Status</th>
            <th>Last Seen</th>
          </tr>
        </thead>
        <tbody>
          {data?.map(e => (
            <tr key={e.id} style={{ borderTop: '1px solid var(--color-border)' }}>
              <td>{e.hostname}</td>
              <td>{e.os}</td>
              <td>{e.status}</td>
              <td>{new Date(e.lastSeen).toLocaleTimeString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
