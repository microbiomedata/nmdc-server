/**
 * plugins/vuetify.ts
 *
 * Framework documentation: https://vuetifyjs.com`
 */
import { createVuetify } from 'vuetify';
import '@mdi/font/css/materialdesignicons.css';
import 'vuetify/styles';
// @ts-ignore
import colors from '@/colors';

export default createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: colors.primary,
          secondary: colors.secondary,
          accent: colors.accent,
          success: colors.success,
          error: colors.error,
        },
      },
    },
  },
})
