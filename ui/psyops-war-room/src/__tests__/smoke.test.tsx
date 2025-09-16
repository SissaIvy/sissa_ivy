import { render, screen } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { OverviewPanel } from '../../src/components/OverviewPanel';

describe('OverviewPanel', () => {
  it('renders health label and endpoints table headers', async () => {
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <OverviewPanel />
      </QueryClientProvider>
    );
    expect(await screen.findByText(/BlackOps Health/i)).toBeInTheDocument();
    expect(screen.getByText(/Endpoints/i)).toBeInTheDocument();
  });
});
