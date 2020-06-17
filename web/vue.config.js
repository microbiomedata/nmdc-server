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
    proxy: 'http://localhost:8000',
  },
  configureWebpack: {
    module: {
      rules: [
        {
          test: /\.tsv$/i,
          use: 'raw-loader',
        },
      ],
    },
  },
};
