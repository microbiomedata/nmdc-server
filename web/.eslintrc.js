module.exports = {
  root: true,
  env: {
    // this section will be used to determine which APIs are available to us
    // (i.e are we running in a browser environment or a node.js env)
    node: true,
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    // specifying a module sourcetype prevent eslint from marking import statements as errors
    ecmaVersion: 2020,
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/recommended',
    '@vue/airbnb',
  ],
  rules: {
    'max-len': 'off',
    'no-underscore-dangle': 0,
    'spaced-comment': 'off',
    'vuejs-accessibility/anchor-has-content': 'off',
    'vuejs-accessibility/click-events-have-key-events': 'off',
    camelcase: 0,
    // we should always disable console logs and debugging in production
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  },
  overrides: [
    {
      files: [
        '**/*.ts',
        '**/*.vue',
      ],
      extends: [
        '@vue/typescript',
      ],
      rules: {
        '@typescript-eslint/no-unused-vars': 2,
      },
    },
  ],
};
