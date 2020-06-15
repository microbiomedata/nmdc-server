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
            <DataObject
              v-if="type === 'data_object'"
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
              <v-col :cols="12">
                <v-card>
                  <FacetChart
                    :type="type"
                    field="omics_type"
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
            v-if="stats"
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
import DataObject from './components/DataObject.vue';
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
    DataObject,
    Welcome,
    Sample,
    Study,
    AttributeList,
  },
  data() {
    return {
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
    };
  },
  computed: {
    singleton() {
      return this.results.length === 1 && this.conditions.findIndex((cond) => cond.field === 'id' && cond.op === '==') >= 0;
    },
  },
  asyncComputed: {
    results: {
      get() {
        if (this.type === null) {
          return [];
        }
        return api.query(this.type, this.conditions);
      },
      default: [],
    },
    allSamples: {
      get() {
        return api.query('sample', []);
      },
      default: [],
    },
    totalDataObjectSize: {
      async get() {
        /* TODO: Fix this */
        let dataObjects = this.results;
        if (this.type !== 'data_object') {
          dataObjects = await api.query('data_object', []);
        }
        return dataObjects.reduce((prev, cur) => prev + (cur.file_size || 0), 0);
      },
    },
    stats: {
      async get() {
        const [databaseSummary, omicsSummary] = await Promise.all([
          api.databaseSummary(),
          api.facetSummary({ type: 'project', field: 'omics_type', conditions: [] }),
        ]);
        return [
          [
            {
              value: databaseSummary.study.total,
              label: 'Studies',
            },
            {
              value: databaseSummary.biosample.attributes.latitude,
              label: 'Locations',
            },
            {
              value: databaseSummary.biosample.attributes.ecosystem_path_id,
              label: 'Habitats',
            },
            {
              value: -1, /* filesize(
                api.query('data_object', []).reduce(
                  (prev, cur) => prev + (cur.file_size || 0), 0,
                ),
              ).replace(/\s+/g, ''), */
              label: 'Data',
            },
          ],
          [
            {
              value: omicsSummary.Metagenome,
              label: 'Metagenomes',
            },
            {
              value: omicsSummary.Metatranscriptome,
              label: 'Metatranscriptomes',
            },
            {
              value: omicsSummary.Proteomics,
              label: 'Proteomics',
            },
            {
              value: omicsSummary.Metabolomics,
              label: 'Metabolomics',
            },
            {
              value: omicsSummary.Lipidomics,
              label: 'Lipidomics',
            },
            {
              value: omicsSummary['Organic Matter Characterization'],
              label: 'Organic Matter Characterization',
            },
          ],
        ];
      },
      default: null,
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
