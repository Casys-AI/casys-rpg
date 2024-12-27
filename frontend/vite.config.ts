import { defineConfig } from 'vite';
import { qwikVite } from '@builder.io/qwik/optimizer';
import { qwikCity } from '@builder.io/qwik-city/vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import { resolve } from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '~': resolve(__dirname, './src')
    }
  },
  plugins: [
    qwikCity(),
    qwikVite({
      devTools: {
        clickToSource: false
      },
      entryStrategy: {
        type: 'smart'
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
    include: [
      '@builder.io/qwik',
      '@builder.io/qwik-city'
    ]
  },
  build: {
    target: 'es2020',
    modulePreload: {
      polyfill: false
    },
    rollupOptions: {
      input: {
        main: 'src/entry.ssr.tsx'
      }
    }
  },
  server: {
    port: 5173,
    host: true,
    fs: {
      strict: false,
      allow: ['..']
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true
      }
    }
  }
});
