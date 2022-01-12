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
        target: 'http://localhost:8000/',
      },
      '/DataHarmonizer': {
        target: 'http://localhost:3333',
        pathRewrite: { '^/DataHarmonizer': '' },
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
