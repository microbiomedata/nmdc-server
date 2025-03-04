import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue2'
import { fileURLToPath, URL } from 'node:url';
import ViteYaml from '@modyfi/vite-plugin-yaml';
import { VuetifyResolver } from 'unplugin-vue-components/resolvers';
import Components from 'unplugin-vue-components/vite';


// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    ViteYaml(),
    Components({
      resolvers: [
        // Vuetify
        VuetifyResolver(),

      ],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '~bootstrap': fileURLToPath(new URL('./node_modules/bootstrap', import.meta.url)),
      'nmdc_schema': fileURLToPath(new URL('./node_modules/nmdc-schema/nmdc_schema/nmdc_materialized_patters.yaml', import.meta.url)),
    },
    extensions: ['.mjs','.ts','.js', '.json', '.vue', '.yaml']
  },
  commonjsOptoins: {
    esmExternals: true
  },
  css: {
    preprocessorOptions: {
      scss: {
        quietDeps: true,
        api: 'modern',
        silenceDeprecations: ['legacy-js-api'],
      },
    }
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
