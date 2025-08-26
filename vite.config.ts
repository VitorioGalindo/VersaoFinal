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
        port: 5173, // Define a porta do frontend explicitamente
        proxy: {
          '/api': {
            target: 'http://127.0.0.1:5001',
            changeOrigin: true,
            secure: false, // Frequentemente ajuda a resolver problemas de proxy
            // Adiciona logs para depurar o que o proxy está fazendo
            configure: (proxy, _options) => {
              proxy.on('error', (err, _req, _res) => {
                console.log('Proxy Error:', err);
              });
              proxy.on('proxyReq', (proxyReq, req, _res) => {
                console.log(`[Vite Proxy] Sending request to backend: ${req.method} ${req.url}`);
              });
              proxy.on('proxyRes', (proxyRes, req, _res) => {
                console.log(`[Vite Proxy] Received response from backend: ${proxyRes.statusCode} ${req.url}`);
              });
            },
          },
        },
      },
    };
});
