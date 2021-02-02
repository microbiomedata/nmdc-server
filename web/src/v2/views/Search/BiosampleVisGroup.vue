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

import {
  conditions, toggleConditions, removeConditions, setUniqueCondition,
} from '@/v2/store';

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
      toggleConditions,
      setUniqueCondition,
      removeConditions,
    };
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col :cols="8">
        <v-card
          outlined
          class="pa-2"
        >
          <LocationMap
            type="biosample"
            :conditions="conditions"
            @selected="toggleConditions($event.conditions)"
          />
        </v-card>
      </v-col>
      <v-col :cols="4">
        <v-card
          outlined
          class="pa-2"
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
    <v-row>
      <v-col cols="12">
        <v-card
          outlined
          class="py-2"
        >
          <BinnedSummaryWrapper
            table="biosample"
            field="collection_date"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="props">
              <DateHistogram
                v-bind="props"
                @select="setUniqueCondition('collection_date', 'biosample', $event.conditions)"
              />
            </template>
          </BinnedSummaryWrapper>
        </v-card>
      </v-col>
      <!-- <v-col :cols="12">
        <EcosystemSankey
          :type="type"
          :conditions="conditions"
          @selected="toggleConditions($event.conditions)"
        />
      </v-col> -->
    </v-row>
  </div>
</template>
