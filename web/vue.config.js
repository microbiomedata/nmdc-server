const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  publicPath: '/',
  transpileDependencies: [
    'vuetify',
  ],
  devServer: {
    overlay: {
      warnings: true,
      errors: true,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000/',
      },
      '/DataHarmonizer': {
        target: 'http://localhost:3333',
        pathRewrite: { '^/DataHarmonizer': '' },
      },
    },
  },
  configureWebpack: {
    plugins: [
      // HACK-DH
      new CopyPlugin({
        patterns: [
          // Import library javascript from DataHarmonizer.
          // Globally scoped dependencies will be loaded from CDN instead of copied.
          { from: './node_modules/sheets_and_friends/docs/script/data-harmonizer/index.js', to: 'script/data-harmonizer/index.js' },
          { from: './node_modules/sheets_and_friends/docs/script/data-harmonizer/toolbar.js', to: 'script/data-harmonizer/toolbar.js' },
          { from: './node_modules/sheets_and_friends/docs/script/data-harmonizer/export_utils.js', to: 'script/data-harmonizer/export_utils.js' },
          { from: './node_modules/sheets_and_friends/docs/script/data-harmonizer/validation.js', to: 'script/data-harmonizer/validation.js' },
          { from: './node_modules/sheets_and_friends/docs/script/data-harmonizer/field_rules.js', to: 'script/data-harmonizer/field_rules.js' },
          { from: './node_modules/sheets_and_friends/docs/template/menu.js', to: 'template/menu.js' },
          { from: './node_modules/sheets_and_friends/docs/template/nmdc_dh/schema.js', to: 'template/nmdc_dh/schema.js' },
          { from: './node_modules/sheets_and_friends/docs/template/nmdc_dh/export.js', to: 'template/nmdc_dh/export.js' },
          { from: './node_modules/sheets_and_friends/docs/template/nmdc_dh/ConfigureFieldSettings.js', to: 'template/nmdc_dh/ConfigureFieldSettings.js' },
          { from: './node_modules/sheets_and_friends/docs/template/nmdc_dh/GoldEcosystemTree.js', to: 'template/nmdc_dh/GoldEcosystemTree.js' },
        ],
      }),
    ],
  },
  chainWebpack: (config) => {
    // https://webpack.js.org/configuration/output/#outputstrictmoduleexceptionhandling
    config.output.strictModuleExceptionHandling(true);
    // Required for https://classic.yarnpkg.com/en/docs/cli/link/
    config.resolve.symlinks(false);
    config.module
      .rule('html')
      .test(/linkml\.html$/)
      .use('raw-loader')
      .loader('raw-loader');
  },
};
