<template>
  <v-app>
    <v-app-bar
      app
      color="white"
      clipped-left
    >
      <v-btn-toggle
        v-model="type"
        :style="{'margin-left': '245px'}"
        background-color="transparent"
        tile
        group
      >
        <v-btn
          v-for="t in Object.keys(types)"
          v-show="types[t].visible"
          :key="t"
          :value="t"
          text
          color="primary"
        >
          <v-icon left>
            {{ types[t].icon }}
          </v-icon>
          {{ types[t].heading }}
        </v-btn>
      </v-btn-toggle>

      <template v-slot:extension>
        <img
          :style="{
            position: 'fixed', 'top': '14px', 'left': '10px', cursor: 'pointer', 'z-index': 10
          }"
          src="NMDC_logo_long.jpg"
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
            @click="conditions = []"
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
            @click="conditions.splice(i, 1)"
            @click:close="conditions.splice(i, 1)"
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
    <template v-if="type">
      <template v-if="singleton">
        <v-content>
          <v-container
            fluid
            style="background: white; height: 100%"
          >
            <Study
              v-if="type === 'study'"
              :item="results[0]"
            />
            <AttributeList
              :type="type"
              :item="results[0]"
              @selected="addSelected($event)"
              @unselected="removeSelected($event)"
            />
          </v-container>
        </v-content>
      </template>
      <template v-else>
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
              v-show="['sample'].includes(type)"
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
            <v-row
              v-show="['sample'].includes(type)"
            >
              <v-col :cols="12">
                <v-card>
                  <EcosystemSankey
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
      </template>
    </template>
    <template v-else>
      <v-content>
        <v-container
          fluid
          style="background: white; height: 100%"
        >
          <Welcome
            :samples="allSamples"
            :stats="stats"
          />
        </v-container>
      </v-content>
    </template>
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
import EcosystemSankey from './components/EcosystemSankey.vue';
import Welcome from './components/Welcome.vue';
import Study from './components/Study.vue';
import AttributeList from './components/AttributeList.vue';

const api = new DataAPI();

export default {
  name: 'App',
  components: {
    FacetedSearch,
    SearchResults,
    LocationMap,
    EcosystemChart,
    EcosystemSankey,
    Welcome,
    Study,
    AttributeList,
  },
  data: () => ({
    type: null,
    types,
    conditions: [],
    stats: [
      {
        value: api.count('study'),
        label: 'Studies',
      },
      {
        value: api.facetSummary('sample', 'latitude', []).length,
        label: 'Locations',
      },
      {
        value: api.facetSummary('sample', 'ecosystem_path_id', []).length,
        label: 'Habitats',
      },
      {
        value: api.query('project', [{ field: 'sequencing_strategy', op: '==', value: 'Metagenome' }]).length,
        label: 'Metagenomes',
      },
      {
        value: api.query('project', [{ field: 'sequencing_strategy', op: '==', value: 'Metatranscriptome' }]).length,
        label: 'Metatranscriptomes',
      },
      {
        value: filesize(
          api.query('data_object', []).reduce(
            (prev, cur) => prev + (cur.file_size || 0), 0,
          ),
        ),
        label: 'Data',
      },
    ],
  }),
  computed: {
    results() {
      if (this.type === null) {
        return [];
      }
      return api.query(this.type, this.conditions);
    },
    singleton() {
      return this.results.length === 1 && this.conditions.findIndex((cond) => cond.field === 'id' && cond.op === '==') >= 0;
    },
    allSamples() {
      return api.query('sample', []);
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
        this.type = to.path.length > 1 ? to.path.substring(1) : null;
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
      if (this.$route.path !== `/${this.type || ''}` || (this.$route.query.q !== queryParam)) {
        this.$router.push({ path: `/${this.type || ''}`, query: { q: queryParam } });
      }
    },
  },
};
</script>
