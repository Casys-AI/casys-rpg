import { defineConfig } from 'vite';
import { qwikVite } from '@builder.io/qwik/optimizer';
import { qwikCity } from '@builder.io/qwik-city/vite';
import tsconfigPaths from 'vite-tsconfig-paths';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    qwikCity(),
    qwikVite(),
    tsconfigPaths()
  ],
  resolve: {
    alias: {
      '~': resolve(__dirname, 'src')
    }
  },
  optimizeDeps: {
    include: [
      '@builder.io/qwik',
      '@builder.io/qwik-city',
      'tailwindcss'
    ],
    exclude: []
  },
  build: {
    target: 'es2020',
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/entry.ssr.tsx')
      }
    }
  },
  server: {
    port: 5173,
    strictPort: false,
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
  },
  preview: {
    port: 5173,
    strictPort: false
  }
});
