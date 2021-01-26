<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';
import LocationMap from '@/components/Presentation/LocationMap.vue';

// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/FacetSummaryWrapper.vue';
import BinnedSummaryWrapper from '@/components/BinnedSummaryWrapper.vue';
// ENDTODO

import { conditions, addConditions, removeConditions } from '@/v2/store';

export default defineComponent({
  name: 'SampleVisGroupV2',
  components: {
    DateHistogram,
    FacetBarChart,
    LocationMap,
    EcosystemSankey,
    // TODO replace with composition functions
    FacetSummaryWrapper,
    BinnedSummaryWrapper,
  },
  setup() {
    return {
      conditions,
      addConditions,
      removeConditions,
    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col :cols="8">
        <LocationMap
          :type="type"
          :conditions="conditions"
          @selected="addConditions($event.conditions)"
        />
      </v-col>
      <v-col :cols="4">
        <FacetSummaryWrapper
          table="biosample"
          field="ecosystem_category"
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
              @selected="addConditions($event.conditions)"
            />
          </template>
        </FacetSummaryWrapper>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12">
        <BinnedSummaryWrapper
          table="biosample"
          field="collection_date"
          use-all-conditions
        >
          <template #default="props">
            <DateHistogram
              v-bind="props"
              @select="addConditions($event.conditions)"
            />
          </template>
        </BinnedSummaryWrapper>
      </v-col>
      <!-- <v-col :cols="12">
        <EcosystemSankey
          :type="type"
          :conditions="conditions"
          @selected="addConditions($event.conditions)"
        />
      </v-col> -->
    </v-row>
  </div>
</template>
