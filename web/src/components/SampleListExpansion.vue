<script lang="ts">
import { groupBy } from 'lodash';
import { computed, defineComponent, PropType } from '@vue/composition-api';
import { fieldDisplayName } from '@/util';
import { BiosampleSearchResult } from '@/data/api';
import DataObjectTable from './DataObjectTable.vue';

const buttonOrder = [
  'metagenome',
  'metatranscriptome',
  'proteomics',
  'metabolomics',
  'organic matter characterization',
];

export default defineComponent({
  components: {
    DataObjectTable,
  },

  props: {
    result: {
      type: Object as PropType<BiosampleSearchResult>,
      required: true,
    },
    expanded: {
      type: Object as PropType<{ resultId: string; omicsProcessingId: string; }>,
      required: true,
    },
    loggedInUser: {
      type: Boolean,
      default: false,
    },
  },

  setup(props) {
    function isOpen(omicsProcessingId: string) {
      return props.expanded.resultId === props.result.id
        && props.expanded.omicsProcessingId === omicsProcessingId;
    }

    const filteredOmicsProcessing = computed(() => Object.entries(groupBy(
      props.result.omics_processing,
      (p) => p.annotations.omics_type,
    )).sort(([agroup], [bgroup]) => {
      const ai = buttonOrder.indexOf(agroup.toLowerCase());
      const bi = buttonOrder.indexOf(bgroup.toLowerCase());
      return ai - bi;
    }));

    return {
      isOpen,
      filteredOmicsProcessing,
      fieldDisplayName,
    };
  },
});
</script>

<template>
  <div
    v-if="result.omics_processing.length"
    class="d-flex flex-column mb-2"
  >
    <div class="d-flex flex-row flex-wrap">
      <v-btn
        v-for="[omicsType, projects] in filteredOmicsProcessing"
        :key="projects[0].id"
        x-small
        :outlined="!isOpen(projects[0].id)"
        :color="isOpen(projects[0].id) ? 'primary' : 'default'"
        :disabled="projects[0].omics_data.length == 0 ? true : false"
        class="mr-2 mt-2"

        @click="() => $emit('open-details', projects[0].id)"
      >
        {{ fieldDisplayName(omicsType) }}
        <v-icon>mdi-chevron-down</v-icon>
      </v-btn>
    </div>
    <template v-for="[omicsType, projects] in filteredOmicsProcessing">
      <DataObjectTable
        v-if="isOpen(projects[0].id)"
        :key="projects[0].id"
        class="flex-row mt-2"
        :omics-processing="projects"
        :omics-type="omicsType"
        :logged-in-user="loggedInUser"
        :biosample="result"
      />
    </template>
  </div>
</template>
