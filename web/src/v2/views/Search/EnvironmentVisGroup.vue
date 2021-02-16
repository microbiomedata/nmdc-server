<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/FacetSummaryWrapper.vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';

import {
  stateRefs, toggleConditions,
} from '@/v2/store';

export default defineComponent({
  components: {
    EcosystemSankey,
    FacetSummaryWrapper,
    FacetBarChart,
  },
  setup() {
    return {
      toggleConditions,
      conditions: stateRefs.conditions,
    };
  },
});
</script>

<template>
  <v-row>
    <v-col :cols="9">
      <EcosystemSankey
        :conditions="conditions"
        @selected="setUniqueCondition($event.conditions)"
      />
    </v-col>
    <v-col :cols="3">
      <v-card
        outlined
        class="pa-1"
      >
        <FacetSummaryWrapper
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
              @selected="toggleConditions($event.conditions)"
            />
          </template>
        </FacetSummaryWrapper>
      </v-card>
    </v-col>
  </v-row>
</template>
