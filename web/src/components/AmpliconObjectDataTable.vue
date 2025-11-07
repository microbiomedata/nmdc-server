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
      { title: 'INSDC Expirement Identifiers', value: 'insdc_experiment_identifiers' },
      { title: 'Target Gene', value: 'target_gene' },
      { title: 'Target Subfragment', value: 'target_subfragment' },
    ];

    const items = computed(() => {
      return props.omicsProcessing[0]?.annotations ? [props.omicsProcessing[0].annotations] : [];
    });

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
