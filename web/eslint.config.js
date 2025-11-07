import js from '@eslint/js';
import vue from 'eslint-plugin-vue';
import typescript from '@typescript-eslint/eslint-plugin';
import typescriptParser from '@typescript-eslint/parser';
import vueParser from 'vue-eslint-parser';
import globals from 'globals';

export default [
  // Ignore build output directories
  {
    ignores: ['**/dist/**', '**/node_modules/**', '**/build/**'],
  },
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.{js,mjs,cjs,vue,ts}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: typescriptParser,
        ecmaVersion: 2020,
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      'max-len': 'off',
      'no-underscore-dangle': 0,
      'spaced-comment': 'off',
      'vuejs-accessibility/anchor-has-content': 'off',
      'vuejs-accessibility/click-events-have-key-events': 'off',
      'vue/no-dupe-keys': 'off',
      'vue/no-v-html': 'off',
      // See: https://github.com/vuejs/eslint-plugin-vue/issues/365
      // The issue is supposed to be resolved, but eslint complains without the ignore
      'vue/html-indent': ['warn', 2, { ignores: ['VElement[name=pre].children'] }],
      'camelcase': 0,
      // we should always disable console logs and debugging in production
      'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
    },
  },
  {
    files: ['**/*.ts', '**/*.vue'],
    plugins: {
      '@typescript-eslint': typescript,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
          vars: 'all',
          args: 'after-used',
          ignoreRestSiblings: true,
        },
      ],
      'no-unused-vars': 'off',
      'no-undef': 'off',
      'no-shadow': 'off',
    },
  },
];
