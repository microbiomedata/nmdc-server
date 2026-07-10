<script lang="ts">
import { defineComponent, PropType, computed } from 'vue';
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
  setup(props) {
    const headers: DataTableHeader[] = [
      { title: 'Type', value: 'type' },
      { title: 'INSDC Experiment Identifiers', value: 'insdc_experiment_identifiers' },
      { title: 'Target Gene', value: 'target_gene' },
      { title: 'Target Subfragment', value: 'target_subfragment' },
    ];

    // Derive the table rows from the `omicsProcessing` props (an array).
    const items = computed(() => props.omicsProcessing.map((op) => ({
      type: op.annotations.type,
      insdc_experiment_identifiers: op.annotations.insdc_experiment_identifiers,
      target_gene: op.annotations.target_gene,
      target_subfragment: op.annotations.target_subfragment,
    })));

    return {
      headers,
      items,
      BioprojectLinkBase,
    };
  },
});

</script>
<template>
  <v-data-table
    :headers="headers"
    :items="items"
  >
    <!-- eslint-disable-next-line -->
    <template #item.insdc_experiment_identifiers="{ item }">
      <a
        :href="BioprojectLinkBase + item?.insdc_experiment_identifiers"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ item && item.insdc_experiment_identifiers && item.insdc_experiment_identifiers[0] }}
      </a>
    </template>
  </v-data-table>
</template>
