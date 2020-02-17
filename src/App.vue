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
          @click="type = t"
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
            <Sample
              v-if="type === 'sample'"
              :item="results[0]"
            />
            <Project
              v-if="type === 'project'"
              :item="results[0]"
            />
            <AttributeList
              :type="type"
              :item="results[0]"
              @selected="setSelected($event)"
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
              <v-col :cols="4">
                <v-card>
                  <EcosystemChart
                    :type="type"
                    :data="results"
                    @selected="addSelected($event)"
                  />
                </v-card>
              </v-col>
              <v-col :cols="8">
                <v-card>
                  <LocationMap
                    :type="type"
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
                    :type="type"
                    :data="results"
                    @selected="addSelected($event)"
                  />
                </v-card>
              </v-col>
            </v-row>
            <v-row
              v-show="['sample'].includes(type)"
            >
              <v-col rows="12">
                <v-card>
                  <v-container fluid>
                    <v-row>
                      <v-col
                        v-for="field in ecosystemFields"
                        :key="field"
                        class="flex-grow-1"
                      >
                        <FacetChart
                          :type="type"
                          :field="field"
                          chart="pie"
                          :conditions="conditions"
                          @selected="addSelected($event)"
                        />
                      </v-col>
                    </v-row>
                  </v-container>
                </v-card>
              </v-col>
            </v-row>
            <v-row
              v-show="['sample'].includes(type)"
            >
              <v-col rows="12">
                <v-card>
                  <v-container fluid>
                    <v-row>
                      <v-col
                        v-for="field in ecosystemFields"
                        :key="field"
                        class="flex-grow-1"
                      >
                        <FacetChart
                          :type="type"
                          :field="field"
                          chart="bar"
                          :conditions="conditions"
                          @selected="addSelected($event)"
                        />
                      </v-col>
                    </v-row>
                  </v-container>
                </v-card>
              </v-col>
            </v-row>
            <v-row
              v-show="['project'].includes(type)"
            >
              <v-col :cols="4">
                <v-card>
                  <FacetChart
                    :type="type"
                    field="sequencing_strategy"
                    chart="bar"
                    :conditions="conditions"
                    :show-title="false"
                    :show-baseline="false"
                    :left-margin="150"
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
                    @selected="setSelected($event)"
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
            @type="type = $event"
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
import api from './data/api';
import FacetedSearch from './components/FacetedSearch.vue';
import SearchResults from './components/SearchResults.vue';
import LocationMap from './components/LocationMap.vue';
import EcosystemChart from './components/EcosystemChart.vue';
import FacetChart from './components/FacetChart.vue';
import EcosystemSankey from './components/EcosystemSankey.vue';
import Welcome from './components/Welcome.vue';
import Sample from './components/Sample.vue';
import Study from './components/Study.vue';
import Project from './components/Project.vue';
import AttributeList from './components/AttributeList.vue';

export default {
  name: 'App',
  components: {
    FacetedSearch,
    SearchResults,
    LocationMap,
    FacetChart,
    EcosystemChart,
    EcosystemSankey,
    Project,
    Welcome,
    Sample,
    Study,
    AttributeList,
  },
  data: () => ({
    type: null,
    types,
    conditions: [],
    ecosystemFields: [
      'ecosystem',
      'ecosystem_category',
      'ecosystem_type',
      'ecosystem_subtype',
      'specific_ecosystem',
    ],
    stats: [
      {
        value: api.count('study'),
        label: 'Studies',
      },
      {
        value: api.facetSummary({ type: 'sample', field: 'latitude' }).length,
        label: 'Locations',
      },
      {
        value: api.facetSummary({ type: 'sample', field: 'ecosystem_path_id' }).length,
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
        this.conditions = [];
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
    async addSelected({ type, conditions }) {
      if (type !== this.type) {
        this.type = type;
        this.conditions = [];
        await this.$nextTick();
      }
      this.conditions = [...this.conditions, ...conditions];
    },
    async setSelected({ type, conditions }) {
      if (type !== this.type) {
        this.type = type;
        this.conditions = [];
        await this.$nextTick();
      }
      this.conditions = conditions;
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
