import { defineConfig } from 'vite';
import { createVuePlugin as vue } from 'vite-plugin-vue2';
import { fileURLToPath, URL } from 'node:url';
import ViteYaml from '@modyfi/vite-plugin-yaml';
import { VuetifyResolver } from 'unplugin-vue-components/resolvers';
import Components from 'unplugin-vue-components/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue(), ViteYaml(), Components({
    resolvers: [
      // Vuetify
      VuetifyResolver(),
    ],
  }),],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: ['.mjs','.ts','.js', '.json', '.vue', '.yaml']
  },
  commonjsOptoins: {
    esmExternals: true
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000/',
      },
      '/static': {
        target: 'http://localhost:8000/',
      },
      '/auth': {
        target: 'http://localhost:8000',
      },
    },
  },
});
