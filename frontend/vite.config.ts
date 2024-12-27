import { defineConfig } from 'vite';
import { qwikVite } from '@builder.io/qwik/optimizer';
import { qwikCity } from '@builder.io/qwik-city/vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    qwikCity(),
    qwikVite({
      devTools: {
        clickToSource: false
      }
    }),
    tsconfigPaths()
  ],
  preview: {
    headers: {
      'Cache-Control': 'public, max-age=600',
    },
  },
  optimizeDeps: {
    include: ['@builder.io/qwik', '@builder.io/qwik-city']
  },
  ssr: {
    noExternal: ['@builder.io/qwik-city']
  },
  build: {
    target: 'es2020',
    modulePreload: {
      polyfill: false
    },
    rollupOptions: {
      input: ['@builder.io/qwik', '@builder.io/qwik-city'],
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        }
      }
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
