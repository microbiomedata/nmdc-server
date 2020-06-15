import Vue from 'vue';
import Vuetify from 'vuetify/lib';
import colors from '../colors';

Vue.use(Vuetify);

export default new Vuetify({
  theme: {
    themes: {
      light: colors,
    },
  },
});
