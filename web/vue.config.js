const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  publicPath: '/',
  transpileDependencies: [
    'vuetify',
  ],
  configureWebpack: {
    resolve: {
      fallback: {
        process: require.resolve('process/browser'),
        buffer: require.resolve('buffer'),
        querystring: require.resolve('querystring-es3'),
      },
    },
    plugins: [
      new webpack.ProvidePlugin({
        process: 'process/browser',
        Buffer: ['buffer', 'Buffer'],
      }),
      new webpack.DefinePlugin({
        'process.env': JSON.stringify(process.env),
      }),
    ],
  },
  devServer: {
    client: {
      overlay: {
        warnings: false,
        errors: true,
      },
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
});
