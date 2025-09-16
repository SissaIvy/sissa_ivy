import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/workspaces/sissa_ivy/ui/psyops-war-room/src'
    }
  },
  build: {
    sourcemap: true,
    target: 'es2021',
    rollupOptions: {
      output: {
        manualChunks: {
          actions: ['/workspaces/sissa_ivy/ui/psyops-war-room/src/components/ActionsForm.tsx','/workspaces/sissa_ivy/ui/psyops-war-room/src/components/ActionTaskPanel.tsx','/workspaces/sissa_ivy/ui/psyops-war-room/src/hooks/useActionTask.ts'],
          overview: ['/workspaces/sissa_ivy/ui/psyops-war-room/src/components/OverviewPanel.tsx','/workspaces/sissa_ivy/ui/psyops-war-room/src/components/HealthGauge.tsx','/workspaces/sissa_ivy/ui/psyops-war-room/src/components/EndpointsOverview.tsx']
        }
      }
    }
  },
  server: {
    port: 5173,
    open: false
  }
});
