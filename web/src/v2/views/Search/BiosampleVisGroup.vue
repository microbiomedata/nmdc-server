<script>
import { defineComponent } from '@vue/composition-api';
import EcosystemSankey from '@/components/Presentation/EcosystemSankey.vue';
import FacetBarChart from '@/components/Presentation/FacetBarChart.vue';
import DateHistogram from '@/components/Presentation/DateHistogram.vue';

import UpSet from '@/components/Presentation/UpSet.vue';
import ChartContainer from '@/components/Presentation/ChartContainer.vue';
// TODO: replace with composition functions
import FacetSummaryWrapper from '@/components/FacetSummaryWrapper.vue';
import BinnedSummaryWrapper from '@/components/BinnedSummaryWrapper.vue';
// ENDTODO
import TooltipCard from '@/v2/components/TooltipCard.vue';
import ClusterMap from '@/v2/components/ClusterMap.vue';

import {
  toggleConditions, removeConditions, setUniqueCondition,
} from '@/v2/store';
import { api } from '@/data/api';

const helpBarchart = 'Displays the number of samples for each data type available. Click on a bar to filter by data type.';
const helpMap = 'Displays geographical location (latitude, longitude) of sample collection sites. Click on a cluster to zoom in.  Click "Search this regon" to limit search to the current map bounds.';
const helpTimeline = 'Displays sample collections grouped by collection month. Scroll the slider to narrow in on a sample collection date range.';
const helpUpset = 'This upset plot shows the number of samples with corresponding omic data associated. For example: there are 43 samples from 1 study that have metagenomics, metatranscriptomics, and natural organic matter characterizations.';

const staticUpsetTooltips = {
  MG: 'Metagenomics',
  MP: 'Metaproteomics',
  MB: 'Metabolomics',
  MT: 'Metatranscriptomics',
  NOM: 'Natural Organic Matter',
};

function makeSetsFromBitmask(mask_str) {
  const mask = parseInt(mask_str, 10); // the bitmask comes in as a string
  const sets = [];

  /* eslint-disable no-bitwise */
  if (1 & mask) {
    sets.push('NOM');
  }
  if ((1 << 4) & mask) {
    sets.push('MB');
  }
  if ((1 << 2) & mask) {
    sets.push('MP');
  }
  if ((1 << 1) & mask) {
    sets.push('MT');
  }
  if ((1 << 3) & mask) {
    sets.push('MG');
  }
  return sets;
}

export default defineComponent({
  name: 'SampleVisGroupV2',
  props: {
    conditions: {
      type: Array, //  as PropType<Condition[]>,
      required: true,
    },
  },
  components: {
    ChartContainer,
    DateHistogram,
    FacetBarChart,
    ClusterMap,
    EcosystemSankey,
    TooltipCard,
    // TODO replace with composition functions
    FacetSummaryWrapper,
    BinnedSummaryWrapper,
    UpSet,
  },
  setup() {
    function setBoundsFromMap(val) {
      setUniqueCondition(['latitude', 'longitude'], ['biosample'], val);
    }
    return {
      helpBarchart,
      helpMap,
      helpTimeline,
      helpUpset,
      toggleConditions,
      setUniqueCondition,
      removeConditions,
      setBoundsFromMap,
      staticUpsetTooltips,
    };
  },
  computed: {
    upsetData() {
      const multiomicsObj = {};
      this.sampleFacetSummary.forEach(({ facet, count }) => {
        if (parseInt(facet, 10) === 0) {
          return;
        }
        multiomicsObj[facet] = {
          counts: {
            Samples: count,
            Studies: 0,
          },
          sets: makeSetsFromBitmask(facet),
        };
      });
      this.studyFacetSummary.forEach(({ facet, count }) => {
        if (parseInt(facet, 10) === 0) {
          return;
        }
        if (!multiomicsObj[facet]) {
          multiomicsObj[facet] = {
            counts: {
              Samples: 0,
            },
            sets: makeSetsFromBitmask(facet),
          };
        }
        multiomicsObj[facet].counts.Studies = count;
      });
      return Object.keys(multiomicsObj)
        .sort((a, b) => parseInt(a, 10) - parseInt(b, 10))
        .map((k) => multiomicsObj[k]);
    },
  },
  asyncComputed: {
    sampleFacetSummary: {
      get() {
        return api.getFacetSummary(
          'biosample',
          'multiomics',
          this.conditions,
        );
      },
      default: [],
    },
    studyFacetSummary: {
      get() {
        return api.getFacetSummary(
          'study',
          'multiomics',
          this.conditions,
        );
      },
      default: [],
    },
  },
});
</script>

<template>
  <div>
    <v-row>
      <v-col :cols="5">
        <TooltipCard :text="helpBarchart">
          <FacetSummaryWrapper
            table="omics_processing"
            field="omics_type"
            :conditions="conditions"
            use-all-conditions
          >
            <template #default="props">
              <FacetBarChart
                v-bind="props"
                :height="360"
                :show-title="false"
                :show-baseline="false"
                :left-margin="120"
                :right-margin="80"
                @selected="toggleConditions($event.conditions)"
              />
            </template>
          </FacetSummaryWrapper>
        </TooltipCard>
      </v-col>
      <v-col :cols="7">
        <TooltipCard
          :text="helpMap"
          class="pa-1"
        >
          <ClusterMap
            :conditions="conditions"
            :height="360"
            @selected="setBoundsFromMap($event)"
          />
        </TooltipCard>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="8">
        <TooltipCard
          :text="helpTimeline"
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
        </TooltipCard>
      </v-col>
      <v-col cols="4">
        <TooltipCard
          :text="helpUpset"
          class="py-0 d-flex flex-column justify-center fill-height"
        >
          <ChartContainer :height="160">
            <template #default="{ width, height }">
              <UpSet
                v-bind="{
                  width,
                  height,
                  data: upsetData,
                  tooltips: staticUpsetTooltips,
                  order: 'Samples',
                }"
              />
            </template>
          </ChartContainer>
          <div
            class="mx-5 upset-legend"
          >
            <span>MG: metagenomics</span>
            <span>MT: metatranscriptomics</span>
            <span>MP: metaproteomics</span>
            <span>MB: metabolomics</span>
            <span>NOM: natural organic matter</span>
          </div>
        </TooltipCard>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
.upset-legend {
  line-height: 0.9em;
}
.upset-legend > span {
  font-size: 10px;
  padding: 0 4px;
  white-space: nowrap;
}
</style>
