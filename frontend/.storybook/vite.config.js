import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    fs: {
      strict: false
    }
  },
  optimizeDeps: {
    include: ['@storybook/svelte']
  },
  resolve: {
    alias: {
      $lib: '/src/lib',
      $app: '/.svelte-kit/runtime/app'
    }
  },
  build: {
    sourcemap: true
  }
});
