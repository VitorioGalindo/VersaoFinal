import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig(() => {
    return {
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      server: {
        host: true,
        proxy: {
          '/api': {
            target: 'http://localhost:5001',
            changeOrigin: true,
            secure: false,
          }
        }
      },
      test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./vitest.setup.ts']
      }
    };
});
