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

    // Derive the table rows from the `omicsProcessing` prop (an array).
    const items = computed(() => props.omicsProcessing.map((op) => ({
      type: op.annotations.type,
      insdc_experiment_identifiers: op.annotations.insdc_experiment_identifiers,
      target_gene: op.annotations.target_gene,
      target_subfragment: op.annotations.target_subfragment,
    })));

    /**
     * Returns the first INSDC Experiment Identifier represented by the specified item (of the kind
     * of "items" that we derive from the `omicsProcessing` prop).
     * 
     * Note: We use this helper function because the relevant field can contain either a string or
     *       an array of strings and we don't want to clutter the template with that logic.
     *       "Why do we give special consideration to the first one?" I don't know. This is a
     *       refactor of existing code, which did not include anyone's rationale for doing that.
     */
    const getFirstInsdcExperimentIdentifier = (item: {insdc_experiment_identifiers?: OmicsProcessingResult["annotations"]["insdc_experiment_identifiers"]}): string | null => {
      const value = item.insdc_experiment_identifiers;
      if (Array.isArray(value)) {
        return typeof value[0] === "string" ? value[0] : null;
      } else {
        return typeof value === "string" ? value : null;
      }
    }

    return {
      headers,
      items,
      BioprojectLinkBase,
      getFirstInsdcExperimentIdentifier,
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
        :href="BioprojectLinkBase + getFirstInsdcExperimentIdentifier(item)"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ item && getFirstInsdcExperimentIdentifier(item) }}
      </a>
    </template>
  </v-data-table>
</template>
