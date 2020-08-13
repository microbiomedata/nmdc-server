<script>
import { mapState, mapGetters, mapActions } from 'vuex';

import { ecosystemFields } from '@/encoding';
import removeCondition from '@/data/utils';

import FacetChart from '@/components/FacetChart.vue';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';

import Sidebar from './Sidebar.vue';

export default {
  components: {
    FacetChart,
    SearchResults,
    LocationMap,
    EcosystemSankey,
    Sidebar,
  },

  data: () => ({ ecosystemFields }),

  computed: {
    ...mapState(['results', 'facetSummaries', 'facetSummariesUnconditional']),
    ...mapGetters(['type', 'conditions']),
    typeResults() {
      const tr = this.results[this.type];
      return tr ? tr.results : null;
    },
  },

  watch: {
    // Vuex will invalidate this cache when necessary,
    // so we can listen to the object to know when to reload.
    facetSummaries: {
      handler: 'updateFacetCharts',
      deep: true,
    },
  },

  methods: {
    ...mapActions(['fetchFacetSummary']),
    updateFacetCharts() {
      if (this.type === 'biosample') {
        this.fetchFacetSummary({
          field: 'ecosystem_category',
          type: 'biosample',
          conditions: this.conditions,
        });
      } else if (this.type === 'project') {
        this.fetchFacetSummary({
          field: 'omics_type',
          type: 'project',
          conditions: this.conditions,
        });
      }
    },
    addSelected({ conditions }) {
      const newConditions = conditions.filter((c) => {
        const match = this.conditions.filter((d) => (
          c.table === d.table
            && c.op === d.op
            && c.value === d.value
            && c.field === d.field));
        return match.length === 0;
      });
      if (newConditions.length > 0) {
        this.$store.dispatch('route', {
          conditions: [
            ...newConditions,
            ...this.conditions,
          ],
        });
      }
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
          <v-col :cols="8">
            <v-card>
              <LocationMap
                :type="type"
                :data="typeResults"
                :conditions="conditions"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
          <v-col :cols="4">
            <v-card>
              <FacetChart
                type="biosample"
                field="ecosystem_category"
                chart="bar"
                :facet-summary="facetSummaries['biosample']['ecosystem_category'] || []"
                :facet-summary-unconditional="
                  facetSummariesUnconditional['biosample']['ecosystem_category'] || []"
                :height="400"
                :show-title="false"
                :show-baseline="false"
                :left-margin="120"
                :right-margin="80"
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
                :conditions="conditions"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>

        <v-row v-if="['project'].includes(type)">
          <v-col>
            <v-card>
              <FacetChart
                type="project"
                field="omics_type"
                chart="bar"
                :facet-summary="facetSummaries['project']['omics_type'] || []"
                :facet-summary-unconditional="
                  facetSummariesUnconditional['project']['omics_type'] || []"
                :show-title="false"
                :show-baseline="false"
                :left-margin="280"
                :right-margin="80"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
        </v-row>

        <v-row>
          <v-col>
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
