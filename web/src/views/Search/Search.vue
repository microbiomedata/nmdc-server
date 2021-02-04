<script>
import Vue from 'vue';
import { mapActions, mapState, mapGetters } from 'vuex';

import { types } from '@/encoding';
import { removeCondition } from '@/data/utils';

import ChartContainer from '@/components/Presentation/ChartContainer.vue';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
import FacetHistogramChart from '@/components/Presentation/FacetHistogramChart.vue';
import FacetSummaryWrapper from '@/components/FacetSummaryWrapper.vue';
import BinnedSummaryWrapper from '@/components/BinnedSummaryWrapper.vue';
// import DateHistogram from '@/components/Presentation/DateHistogram.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';
import UpSet from '@/components/Presentation/UpSet.vue';

import Sidebar from './Sidebar.vue';

export default Vue.extend({
  components: {
    BinnedSummaryWrapper,
    ChartContainer,
    FacetBarChart,
    FacetHistogramChart,
    FacetSummaryWrapper,
    // DateHistogram,
    DateHistogram,
    SearchResults,
    UpSet,
    LocationMap,
    EcosystemSankey,
    Sidebar,
  },

  data: () => ({
    types,
    upSetData: [
      {
        sets: ['MG', 'MP'],
        counts: { Samples: 33, Studies: 1 },
      },
      {
        sets: ['MG', 'MP', 'MT', 'OM'],
        counts: { Samples: 45, Studies: 1 },
      },
      {
        sets: ['MG'],
        counts: { Samples: 143, Studies: 3 },
      },
      {
        sets: ['MB'],
        counts: { Samples: 87, Studies: 3 },
      },
    ],
  }),

  computed: {
    ...mapState(['results', 'page', 'pageSize']),
    ...mapGetters(['type', 'conditions']),
    typeResults() {
      return this.results[this.type] || null;
    },
  },

  methods: {
    ...mapActions(['route', 'refreshResults']),
    addSelected({ conditions }) {
      const duplicates = [];
      const newConditions = conditions.filter((c) => {
        const match = this.conditions.filter((d) => (
          c.table === d.table
            && c.op === d.op
            && c.value === d.value
            && c.field === d.field));
        if (match.length === 0) {
          return true; // this is a new condition
        }
        duplicates.push(c);
        return false;
      });
      if (newConditions.length > 0 || duplicates.length > 0) {
        this.route({
          conditions: [
            ...newConditions,
            ...removeCondition(this.conditions, duplicates),
          ],
        });
      }
    },
    navigateToSelected(id) {
      this.route({
        name: 'Individual Result',
        type: this.type,
        conditions: [{
          field: 'id', op: '==', value: id, table: this.type,
        }],
      });
    },
  },
});
</script>

<template>
  <div>
    <sidebar />
    <v-main v-if="typeResults">
      <v-container fluid>
        <v-row>
          <v-col :cols="12">
            <ChartContainer>
              <template #default="{ width, height }">
                <UpSet v-bind="{ width, height, data: upSetData, order: 'Samples' }" />
              </template>
            </ChartContainer>
          </v-col>
        </v-row>
        <!-- BIOSAMPLE CHARTS -->
        <template v-if="type === 'biosample'">
          <v-row>
            <v-col :cols="8">
              <LocationMap
                :type="type"
                :conditions="conditions"
                @selected="addSelected($event)"
              />
            </v-col>
            <v-col :cols="4">
              <facet-summary-wrapper
                table="biosample"
                field="ecosystem_category"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetBarChart
                    v-bind="props"
                    :height="400"
                    :show-title="false"
                    :show-baseline="false"
                    :left-margin="120"
                    :right-margin="80"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12">
              <binned-summary-wrapper
                table="biosample"
                field="collection_date"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <DateHistogram
                    v-bind="props"
                    @select="$store.dispatch('route', $event)"
                  />
                </template>
              </binned-summary-wrapper>
            </v-col>
            <v-col :cols="12">
              <EcosystemSankey
                :type="type"
                :conditions="conditions"
                @selected="addSelected($event)"
              />
            </v-col>
          </v-row>
        </template>

        <!-- PROJECT CHARTS -->
        <template v-if="type === 'project'">
          <v-row>
            <v-col>
              <facet-summary-wrapper
                table="project"
                field="omics_type"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetBarChart
                    v-bind="props"
                    :height="250"
                    :show-title="false"
                    :show-baseline="false"
                    :left-margin="240"
                    :right-margin="80"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
            </v-col>
          </v-row>
        </template>

        <!-- METAGENOME ASSEMBY CHARTS -->
        <template v-if="type === 'metagenome_assembly'">
          <v-row v-if="typeResults.count">
            <v-col>
              <facet-summary-wrapper
                table="metagenome_assembly"
                field="contigs"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetHistogramChart
                    v-bind="props"
                    :height="230"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
              <facet-summary-wrapper
                table="metagenome_assembly"
                field="contig_bp"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetHistogramChart
                    v-bind="props"
                    :height="230"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
              <facet-summary-wrapper
                table="metagenome_assembly"
                field="num_input_reads"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetHistogramChart
                    v-bind="props"
                    :height="230"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
            </v-col>
          </v-row>
        </template>

        <!-- READS QC CHARTS -->
        <template v-if="type === 'reads_qc'">
          <v-row v-if="typeResults.count">
            <v-col>
              <facet-summary-wrapper
                table="reads_qc"
                field="output_read_bases"
                :conditions="conditions"
                use-all-conditions
              >
                <template #default="props">
                  <FacetHistogramChart
                    v-bind="props"
                    :height="230"
                    @selected="addSelected($event)"
                  />
                </template>
              </facet-summary-wrapper>
            </v-col>
          </v-row>
        </template>

        <!-- SEARCH RESULTS GENERIC -->
        <v-row>
          <v-col>
            <SearchResults
              :count="typeResults.count"
              :icon="types[type].icon"
              :items-per-page="pageSize"
              :results="typeResults.results"
              :page="page"
              @set-page="refreshResults({ page: $event })"
              @selected="navigateToSelected($event)"
            />
            <h2 v-if="typeResults.count === 0">
              No results for selected conditions in {{ type }}
            </h2>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </div>
</template>
