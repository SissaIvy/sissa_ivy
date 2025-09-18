// Route chunk prefetch helpers
export function prefetchRoute(name: 'overview' | 'endpoints' | 'actions') {
  switch (name) {
    case 'overview':
      void import('@/pages/OperationsOverview');
      break;
    case 'endpoints':
      void import('@/pages/Endpoints');
      break;
    case 'actions':
      void import('@/pages/Actions');
      break;
    default:
      break;
  }
}
