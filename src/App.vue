<template>
  <v-app>
    <v-app-bar
      app
      color="primary"
      dark
      clipped-left
    >
      <v-toolbar-title class="font-weight-bold mr-8">
        <v-icon
          large
          left
        >
          mdi-google-circles-extended
        </v-icon>
        National Microbiome Data Collaborative
      </v-toolbar-title>

      <v-btn-toggle
        v-model="typeIndex"
        background-color="transparent"
        tile
        group
        mandatory
      >
        <v-btn
          v-for="(t, ind) in types"
          :key="t.id"
        >
          <v-icon left>
            {{ t.icon }}
          </v-icon>
          {{ `${
            typeIndex === ind && count(t.id) > results.length ? `${results.length} of ` : ''
          }${count(t.id)} ${t.plural}` }}
        </v-btn>
      </v-btn-toggle>

      <template v-slot:extension>
        <v-chip
          v-if="conditions.length"
          label
          outlined
          class="ma-2"
          color="white"
          text-color="white"
          @click="conditions = []"
        >
          Clear all
        </v-chip>

        <v-chip
          v-for="(condition, i) in conditions"
          :key="i"
          close
          label
          class="ma-2"
          color="grey lighten-2"
          text-color="black"
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
      Login
    </v-app-bar>

    <v-navigation-drawer
      app
      clipped
      permanent
    >
      <FacetedSearch
        v-model="conditions"
        :type="types[typeIndex].id"
      />
    </v-navigation-drawer>

    <v-content>
      <v-container fluid>
        <v-row
          v-show="['sample'].includes(types[typeIndex].id)"
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
          v-show="['study', 'sample'].includes(types[typeIndex].id)"
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
                :type="types[typeIndex].id"
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
import { fieldDisplayName, valueDisplayName } from './util';
import { types } from './components/encoding';
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
    typeIndex: 0,
    types: Object.keys(types).map((type) => ({ id: type, ...types[type] })),
    conditions: [],
  }),
  computed: {
    type() {
      return this.types[this.typeIndex].id;
    },
    results() {
      return api.query(this.type, this.conditions);
    },
  },
  methods: {
    fieldDisplayName,
    valueDisplayName,
    count(type) {
      return api.count(type);
    },
    async addSelected({ type = this.type, value, field = 'id' }) {
      if (type !== this.type) {
        this.typeIndex = this.types.findIndex((t) => t.id === type);
      }
      await this.$nextTick();
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
  },
};
</script>
