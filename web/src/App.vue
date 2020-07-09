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
      <div :style="{'margin-left': '245px'}">
        <v-btn
          v-for="t in Object.keys(types)"
          v-show="types[t].visible || type === t"
          :key="t"
          :value="t"
          :text="type !== t"
          elevation="0"
          :color="type === t ? 'primary' : 'primary'"
          class="mx-2"
          @click="changeType(t)"
        >
          <v-icon left>
            {{ types[t].icon }}
          </v-icon>
          {{ types[t].heading }}
        </v-btn>
      </div>

      <template v-slot:extension>
        <img
          :style="{
            position: 'fixed', 'top': '14px', 'left': '10px', cursor: 'pointer', 'z-index': 10
          }"
          src="/NMDC_logo_long.jpg"
          height="80"
          @click="$router.push('/')"
        >
        <div v-if="type">
          <v-btn
            v-if="conditions.length"
            :style="{'margin-left': '250px !important'}"
            icon
            small
            class="ma-1"
            color="primary"
            text-color="primary"
            @click="resetConditions"
          >
            <v-icon>
              mdi-close
            </v-icon>
          </v-btn>

          <v-chip
            v-for="(condition, i) in conditions"
            :key="i"
            close
            label
            class="ma-1"
            color="primary"
            dark
            @click="removeConditionIndex(i)"
            @click:close="removeConditionIndex(i)"
          >
            {{
              fieldDisplayName(condition.field)
            }} : {{
              valueDisplayName(condition.field, condition.value).substring(0, 20)
            }}
          </v-chip>
        </div>
      </template>
    </v-app-bar>
    <router-view />
  </v-app>
</template>
