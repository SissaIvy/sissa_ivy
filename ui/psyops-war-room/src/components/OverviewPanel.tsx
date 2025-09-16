import React from 'react';
import { HealthGauge } from './HealthGauge';
import { EndpointsOverview } from './EndpointsOverview';

export const OverviewPanel: React.FC = () => {
  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      <div>
        <h2 style={{ fontSize: 16, margin: '0 0 12px 0' }}>BlackOps Health</h2>
        <HealthGauge />
      </div>
      <div>
        <EndpointsOverview />
      </div>
    </section>
  );
};
