import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/workspaces/sissa_ivy/ui/psyops-war-room/src'
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: true,
    coverage: { provider: 'v8', reporter: ['text', 'html'], exclude: ['src/theme/**'] }
  }
});
