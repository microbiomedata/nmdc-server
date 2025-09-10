<script lang="ts">
import { groupBy } from 'lodash';
import { computed, defineComponent, PropType } from '@vue/composition-api';
import { fieldDisplayName } from '@/util';
import { BiosampleSearchResult } from '@/data/api';
import DataObjectTable from './DataObjectTable.vue';
import AmpliconObjectDataTable from './AmpliconObjectDataTable.vue';

const buttonOrder = [
  'metagenome',
  'metatranscriptome',
  'proteomics',
  'metabolomics',
  'organic matter characterization',
  'amplicon',
];

export default defineComponent({
  components: {
    DataObjectTable,
    AmpliconObjectDataTable,
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
    function isDisabled(omicsType: string, projects: any[]) {
      // TODO this is a temporary fix for the amplicon button
      // until we have a proper way to handle amplicon data.
      if (projects[0].omics_data.length === 0) {
        console.log('Disabling button for', omicsType, projects);
      }
      return projects[0].omics_data.length === 0 && omicsType !== 'Amplicon';
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
      isDisabled,
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
      <v-tooltip
        v-for="[omicsType, projects] in filteredOmicsProcessing"
        :key="projects[0].id"
        max-width="350"
        bottom
        content-class="clickable-tooltip"
        close-delay="1000"
      >
        <template #activator="{ on, attrs }">
          <span
            v-bind="attrs"
            v-on="isDisabled(omicsType, projects) ? on : ''"
          >
            <v-btn
              x-small
              :outlined="!isOpen(projects[0].id)"
              :color="isOpen(projects[0].id) ? 'primary' : 'default'"
              :disabled="isDisabled(omicsType, projects)"
              class="mr-2 mt-2"
              @click="() => $emit('open-details', projects[0].id)"
            >
              {{ fieldDisplayName(omicsType) }}
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
          </span>
        </template>
        <span>
          Workflows have not been processed yet. Please contact
          <a
            class="blue--text text--lighten-2"
            href="mailto:support@microbiomedata.org"
          >
            support@microbiomedata.org
          </a>
          if you have questions.
        </span>
      </v-tooltip>
    </div>
    <template v-for="[omicsType, projects] in filteredOmicsProcessing">
      <DataObjectTable
        v-if="isOpen(projects[0].id) && omicsType !== 'Amplicon'"
        :key="projects[0].id"
        class="flex-row mt-2"
        :omics-processing="projects"
        :omics-type="omicsType"
        :logged-in-user="loggedInUser"
        :biosample="result"
      />
      <AmpliconObjectDataTable
        v-if="isOpen(projects[0].id) && omicsType === 'Amplicon'"
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

<style scoped>
.clickable-tooltip {
  pointer-events: all;
}
</style>
