<script>
import filesize from 'filesize';
import { mapGetters } from 'vuex';

import removeCondition from '@/data/utils';
import { fieldDisplayName, valueDisplayName } from '@/util';
import { types } from '@/encoding';

export default {
  name: 'App',

  data() {
    return { types };
  },

  computed: {
    ...mapGetters(['typeResults', 'type', 'conditions']),
  },

  methods: {
    fieldDisplayName,
    valueDisplayName,
    filesize,
    changeType(newtype) {
      this.$router.push({ name: 'Search', params: { type: newtype } });
    },
    resetConditions() {
      this.$router.push({ name: 'Search', query: { conditions: [] } });
    },
    removeConditionIndex(index) {
      const conditions = removeCondition(this.conditions, this.conditions[index]);
      if (conditions.length === 0 && this.$router.currentRoute.name !== 'Search') {
        this.resetConditions();
      } else {
        this.$router.push({ query: { conditions } });
      }
    },
  },
};
</script>

<template>
  <v-app>
    <v-app-bar
      app
      color="white"
      clipped-left
      elevation="1"
    >
      <router-link
        to="/"
        style="height: 100%"
      >
        <img
          src="/NMDC_logo_long.jpg"
          height="100%"
        >
      </router-link>
    </v-app-bar>
    <router-view />
  </v-app>
</template>
