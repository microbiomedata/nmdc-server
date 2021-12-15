// const path = require('path');

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
        target: 'https://data.microbiomedata.org',
      },
      '/data-harmonizer': {
        target: 'http://localhost:3333',
        pathRewrite: { '^/data-harmonizer': '' },
      },
    },
  },
  chainWebpack: (config) => {
    // https://webpack.js.org/configuration/output/#outputstrictmoduleexceptionhandling
    config.output.strictModuleExceptionHandling(true);
    // Required for https://classic.yarnpkg.com/en/docs/cli/link/
    config.resolve.symlinks(false);
  },
};
