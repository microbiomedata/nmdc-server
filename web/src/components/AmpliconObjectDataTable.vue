<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { DataTableHeader } from 'vuetify';
import { OmicsProcessingResult } from '@/data/api';

const BioprojectLinkBase = 'https://bioregistry.io/';

export default defineComponent({
  name: 'AmpliconObjectDataTable',
  props: {
    omicsProcessing: {
      type: Array as PropType<OmicsProcessingResult[]>,
      required: true,
    },
    omicsType: {
      type: String,
      required: true,
    },
  },
  setup() {
    const headers: DataTableHeader[] = [
      { text: 'Type', value: 'type' },
      { text: 'INSDC Expirement Identifiers', value: 'insdc_experiment_identifiers' },
      { text: 'Target Gene', value: 'target_gene' },
      { text: 'Target Subfragment', value: 'target_subfragment' },
    ];

    return {
      headers,
      BioprojectLinkBase,
    };
  },
});

</script>
<template>
  <v-data-table
    :headers="headers"
    :items="[omicsProcessing[0].annotations]"
  >
    <!-- eslint-disable-next-line -->
    <template #item.insdc_experiment_identifiers="{ item }">
      <a
        :href="BioprojectLinkBase + item.insdc_experiment_identifiers"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ item.insdc_experiment_identifiers[0] }}
      </a>
    </template>
  </v-data-table>
</template>
