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
      '/static': {
        target: 'http://localhost:8000/',
      },
      '/auth': {
        target: 'http://localhost:8000',
      },
    },
  },
  chainWebpack: (config) => {
    // https://webpack.js.org/configuration/output/#outputstrictmoduleexceptionhandling
    config.output.strictModuleExceptionHandling(true);
    // Required for https://classic.yarnpkg.com/en/docs/cli/link/
    // config.resolve.symlinks(false);
  },
};
