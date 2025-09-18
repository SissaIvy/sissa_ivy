import { StrictMode, Suspense, lazy } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { App } from './App';
import Spinner from '@/components/Spinner';

const OperationsOverview = lazy(() => import('@/pages/OperationsOverview'));
const Endpoints = lazy(() => import('@/pages/Endpoints'));
const Actions = lazy(() => import('@/pages/Actions'));

const withSuspense = (el: JSX.Element, label: string) => (
  <Suspense fallback={<Spinner label={label} />}>{el}</Suspense>
);

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false } }
});

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: withSuspense(<OperationsOverview />, 'Loading overview…') },
      { path: 'endpoints', element: withSuspense(<Endpoints />, 'Loading endpoints…') },
      { path: 'actions', element: withSuspense(<Actions />, 'Loading actions…') }
    ]
  }
]);

createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>
);
