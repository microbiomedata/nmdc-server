<template>
  <v-app>
    <v-app-bar
      app
      color="white"
      clipped-left
    >
      <img
        :style="{position: 'absolute', 'top': '14px', 'left': '10px'}"
        src="NMDC_logo_long.jpg"
        height="80"
      >

      <v-btn-toggle
        v-model="type"
        :style="{'margin-left': '245px'}"
        background-color="transparent"
        tile
        group
        mandatory
      >
        <v-btn
          v-for="(t) in Object.keys(types)"
          :key="t"
          :value="t"
          text
          color="primary"
        >
          <v-icon left>
            {{ types[t].icon }}
          </v-icon>
          {{ `${
            type === t && count(t) > results.length ? `${results.length} of ` : ''
          }${count(t)} ${types[t].plural}` }}
          {{ t === 'data_object' ?
            ` (${filesize(totalDataObjectSize)})` : '' }}
        </v-btn>
      </v-btn-toggle>

      <template v-slot:extension>
        <v-chip
          v-if="conditions.length"
          :style="{'margin-left': '250px !important'}"
          label
          outlined
          class="ma-1"
          color="primary"
          text-color="primary"
          @click="conditions = []"
        >
          Clear all
        </v-chip>

        <v-chip
          v-for="(condition, i) in conditions"
          :key="i"
          close
          label
          class="ma-1"
          color="primary"
          dark
          @click="conditions.splice(i, 1)"
          @click:close="conditions.splice(i, 1)"
        >
          {{
            fieldDisplayName(condition.field)
          }} : {{
            valueDisplayName(condition.field, condition.value).substring(0, 20)
          }}
        </v-chip>
      </template>

      <v-spacer />
    </v-app-bar>

    <v-navigation-drawer
      app
      clipped
      permanent
    >
      <FacetedSearch
        v-model="conditions"
        :type="type"
      />
    </v-navigation-drawer>

    <v-content>
      <v-container fluid>
        <v-row
          v-show="['sample'].includes(type)"
        >
          <v-col :cols="12">
            <v-card>
              <LocationMap
                :data="results"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>
        <v-row
          v-show="['study', 'sample'].includes(type)"
        >
          <v-col :cols="12">
            <v-card>
              <EcosystemChart
                :data="results"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>
        <v-row>
          <v-col :cols="12">
            <v-card>
              <SearchResults
                :type="type"
                :results="results"
                :conditions="conditions"
                @selected="addSelected($event)"
                @unselected="removeSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-content>
  </v-app>
</template>

<script>
import filesize from 'filesize';
import { fieldDisplayName, valueDisplayName } from './util';
import { types } from './encoding';
import DataAPI from './data/DataAPI';
import FacetedSearch from './components/FacetedSearch.vue';
import SearchResults from './components/SearchResults.vue';
import LocationMap from './components/LocationMap.vue';
import EcosystemChart from './components/EcosystemChart.vue';

const api = new DataAPI();

export default {
  name: 'App',
  components: {
    FacetedSearch,
    SearchResults,
    LocationMap,
    EcosystemChart,
  },
  data: () => ({
    type: 'study',
    types,
    conditions: [],
  }),
  computed: {
    results() {
      return api.query(this.type, this.conditions);
    },
    totalDataObjectSize() {
      let dataObjects = this.results;
      if (this.type !== 'data_object') {
        dataObjects = api.query('data_object', []);
      }
      return dataObjects.reduce((prev, cur) => prev + (cur.file_size || 0), 0);
    },
  },
  watch: {
    $route: {
      handler(to) {
        if (to.path === '/') {
          this.$router.push({ path: `/${this.type}` });
          return;
        }
        this.type = to.path.substring(1);
        if (to.query.q) {
          this.conditions = JSON.parse(to.query.q);
        } else {
          this.conditions = [];
        }
      },
      immediate: true,
    },
    type: {
      handler() {
        this.navigateIfChanged();
      },
    },
    conditions: {
      handler() {
        this.navigateIfChanged();
      },
    },
  },
  methods: {
    fieldDisplayName,
    valueDisplayName,
    filesize,
    count(type) {
      return api.count(type);
    },
    async addSelected({ type = this.type, value, field = 'id' }) {
      if (type !== this.type) {
        this.type = type;
        this.conditions = [];
        await this.$nextTick();
      }
      this.conditions.push({ field, op: '==', value });
    },
    removeSelected({ type = this.type, value, field = 'id' }) {
      if (type !== this.type) {
        return;
      }
      const foundIndex = this.conditions.findIndex((cond) => cond.field === field && cond.op === '==' && cond.value === value);
      if (foundIndex >= 0) {
        this.conditions.splice(foundIndex, 1);
      }
    },
    navigateIfChanged() {
      const queryParam = JSON.stringify(this.conditions);
      if (this.$route.path !== `/${this.type}` || (this.$route.query.q !== queryParam)) {
        this.$router.push({ path: `/${this.type}`, query: { q: queryParam } });
      }
    },
  },
};
</script>
