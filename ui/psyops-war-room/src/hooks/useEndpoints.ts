import { useQuery } from '@tanstack/react-query';
import { EndpointSummary } from '../types/domain';
import { getMockEndpoints } from '../mocks/endpoints';

export function useEndpoints() {
  return useQuery<EndpointSummary[]>({
    queryKey: ['endpoints'],
    queryFn: async () => {
      const base = import.meta.env.VITE_API_BASE as string | undefined;
      if (!base) {
        // Mock path
        return getMockEndpoints();
      }
      const res = await fetch(`${base}/api/endpoints`);
      if (!res.ok) throw new Error('Failed to fetch endpoints');
      return (await res.json()) as EndpointSummary[];
    },
    staleTime: 15_000
  });
}
