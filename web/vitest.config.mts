import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.mts';

export default defineConfig(
  mergeConfig(viteConfig, {
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: ['node_modules/', 'test/'],
      },
      server: {
        deps: {
          inline: ['vuetify'],
        },
      },
    },
  })
);