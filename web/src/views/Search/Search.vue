<script>
import { mapState, mapGetters } from 'vuex';

import { ecosystemFields } from '@/encoding';
import removeCondition from '@/data/utils';

import FacetChart from '@/components/FacetChart.vue';
import EcosystemChart from '@/components/Presentation/EcosystemChart.vue';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';

import Sidebar from './Sidebar.vue';

export default {
  components: {
    FacetChart,
    SearchResults,
    LocationMap,
    EcosystemChart,
    EcosystemSankey,
    Sidebar,
  },

  data: () => ({ ecosystemFields }),

  computed: {
    ...mapState(['results']),
    ...mapGetters(['type', 'conditions']),
    typeResults() {
      const tr = this.results[this.type];
      return tr ? tr.results : null;
    },
  },

  methods: {
    addSelected({ conditions }) {
      this.$store.dispatch('route', {
        conditions: [
          ...this.conditions,
          ...conditions,
        ],
      });
    },
    removeCondition(c) {
      this.$store.dispatch('route', {
        conditions: removeCondition(this.conditions, c),
      });
    },
    navigateToSelected(id) {
      this.$store.dispatch('route', {
        name: 'Individual Result',
        type: this.type,
        conditions: [{
          field: 'id', op: '==', value: id, table: this.type,
        }],
      });
    },
  },
};
</script>

<template>
  <div>
    <sidebar />
    <v-main v-if="typeResults">
      <v-container fluid>
        <v-row v-if="['biosample'].includes(type)">
          <v-col :cols="4">
            <v-card>
              <EcosystemChart
                :type="type"
                :data="typeResults"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
          <v-col :cols="8">
            <v-card>
              <LocationMap
                :type="type"
                :data="typeResults"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>

        <v-row v-if="['biosample'].includes(type)">
          <v-col :cols="12">
            <v-card>
              <EcosystemSankey
                :type="type"
                :data="typeResults"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>

        <v-row v-if="['biosample'].includes(type)">
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
                      type="biosample"
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

        <v-row v-if="['biosample'].includes(type)">
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
                      type="biosample"
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

        <v-row v-if="['project'].includes(type)">
          <v-col :cols="12">
            <v-card>
              <FacetChart
                type="project"
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
                :results="typeResults"
                :conditions="conditions"
                @selected="navigateToSelected($event)"
                @unselected="removeCondition($event)"
              />
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </div>
</template>
