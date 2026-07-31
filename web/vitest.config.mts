import { defineConfig, mergeConfig } from 'vitest/config';
import viteConfig from './vite.config.mts';
import { playwright } from '@vitest/browser-playwright';

export default defineConfig(
  mergeConfig(viteConfig, {
    test: {
      globals: true,
      browser: {
        provider: playwright({
          launchOptions: {
            headless: true,
          },
        }),
        enabled: true,
        instances: [
          { browser: 'chromium' },
          { browser: 'firefox' },
          { browser: 'webkit' },
        ],
      },
      setupFiles: ['./src/test/setup.ts'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'json', 'html'],
        exclude: ['node_modules/', 'test/'],
      },
    },
    optimizeDeps: {
      include: ['@testing-library/vue'],
    },
  })
);