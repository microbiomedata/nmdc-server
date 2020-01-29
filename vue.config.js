module.exports = {
  publicPath: process.env.NODE_ENV === 'production'
    ? '/pilot/'
    : '/',
  transpileDependencies: [
    'vuetify',
  ],
  devServer: {
    overlay: {
      warnings: true,
      errors: true,
    },
  },
};
