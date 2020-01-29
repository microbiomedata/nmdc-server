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
          v-for="(type, ind) in types"
          :key="type.id"
        >
          <v-icon left>
            {{ type.icon }}
          </v-icon>
          {{ `${
            typeIndex === ind && count(type.id) > results.length ? `${results.length} of ` : ''
          }${count(type.id)} ${type.name}` }}
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
          v-if="results.length > 1 && ['sample'].includes(types[typeIndex].id)"
        >
          <v-col :cols="12">
            <v-card
              v-if="types[typeIndex].id === 'sample'"
            >
              <LocationMap :data="results" />
            </v-card>
          </v-col>
        </v-row>
        <v-row
          v-if="results.length > 1 && ['study', 'sample'].includes(types[typeIndex].id)"
        >
          <v-col :cols="12">
            <v-card>
              <EcosystemChart :data="results" />
            </v-card>
          </v-col>
        </v-row>
        <v-row>
          <v-col :cols="12">
            <v-card>
              <SearchResults
                :type="types[typeIndex].id"
                :results="results"
                @selected="addSelected($event)"
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
    types: [
      {
        id: 'study',
        name: 'Studies',
        icon: 'mdi-book',
      },
      {
        id: 'project',
        name: 'Projects',
        icon: 'mdi-dna',
      },
      {
        id: 'sample',
        name: 'Samples',
        icon: 'mdi-test-tube',
      },
      {
        id: 'file',
        name: 'Files',
        icon: 'mdi-file',
      },
    ],
    conditions: [],
  }),
  computed: {
    results() {
      return api.query(this.types[this.typeIndex].id, this.conditions);
    },
  },
  methods: {
    count(type) {
      return api.count(type);
    },
    async addSelected({ type, id }) {
      if (type !== this.type) {
        this.typeIndex = this.types.findIndex((t) => t.id === type);
      }
      await this.$nextTick();
      this.conditions.push({ field: 'id', op: '==', value: id });
    },
    fieldDisplayName,
    valueDisplayName,
  },
};
</script>
