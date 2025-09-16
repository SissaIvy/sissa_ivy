import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ActionTaskPanel from '@/components/ActionTaskPanel';

describe('ActionTaskPanel lifecycle', () => {
  it('reaches SUCCEEDED status after simulated time', async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <ActionTaskPanel taskId="task-123" />
      </QueryClientProvider>
    );
    // Should render the panel and initial status quickly
    await screen.findByRole('heading', { name: /Action Status/i }, { timeout: 1000 });
    // Within ~2s the simulation should flip to SUCCEEDED
  const succeededEls = await screen.findAllByText(/SUCCEEDED/i, undefined, { timeout: 4000 });
  expect(succeededEls.length).toBeGreaterThan(0);
  });
});
