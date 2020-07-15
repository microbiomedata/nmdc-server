<script>
import { mapState, mapGetters } from 'vuex';

import { ecosystemFields } from '@/encoding';
import removeCondition from '@/data/utils';

import FacetChart from '@/components/FacetChart.vue';

import EcosystemChart from '@/components/Presentation/EcosystemChart.vue';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import FacetedSearch from '@/components/Presentation/FacetedSearch.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';
import SearchResults from '@/components/Presentation/SearchResults.vue';

export default {
  components: {
    FacetedSearch,
    FacetChart,
    SearchResults,
    LocationMap,
    EcosystemChart,
    EcosystemSankey,
  },

  data: () => ({ ecosystemFields }),

  computed: {
    ...mapState(['results', 'facetSummaries']),
    ...mapGetters(['type', 'conditions']),
    typeResults() {
      const tr = this.results[this.type];
      return tr ? tr.results : null;
    },
  },

  watch: {
    type() { this.$store.dispatch('refreshAll'); },
    conditions() { this.$store.dispatch('refreshAll'); },
  },

  async created() {
    await this.$store.dispatch('load');
    this.$store.dispatch('refreshAll');
  },

  methods: {
    addSelected({ conditions }) {
      this.$router.push({
        query: {
          conditions: [
            ...this.conditions,
            ...conditions,
          ],
        },
      });
    },
    removeCondition(c) {
      this.$router.push({ query: { conditions: removeCondition(this.conditions, c) } });
    },
    navigateToSelected(id) {
      this.$router.push({
        name: 'Individual Result',
        params: {
          type: this.type,
        },
        query: {
          conditions: [{ field: 'id', op: '==', value: id }],
        },
      });
    },
  },
};
</script>

<template>
  <div>
    <v-navigation-drawer
      app
      clipped
      permanent
    >
      <FacetedSearch
        :conditions="conditions"
        :type="type"
        :facet-summaries="facetSummaries[type]"
      />
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <v-row v-if="['biosample'].includes(type)">
          <v-col :cols="4">
            <v-card>
              <EcosystemChart
                v-if="typeResults"
                :type="type"
                :data="typeResults"
                @selected="addSelected($event)"
              />
            </v-card>
          </v-col>
          <v-col :cols="8">
            <v-card>
              <LocationMap
                v-if="typeResults"
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
                v-if="typeResults"
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

        <v-row v-show="['project'].includes(type)">
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

        <v-row v-if="typeResults">
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
