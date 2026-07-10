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
     * Note: We made this helper function because the relevant field can contain either a string or
     *       an array of strings and we don't want to clutter the template with the necessary code
     *       to pluck the right value from it. As for why we give special consideration to the
     *       _first_ item in the array: I don't know. This is a refactor of some existing code,
     *       and that existing code did not include an explanation/rationale for doing that.
     */
    const getFirstInsdcExperimentIdentifier = (item: {insdc_experiment_identifiers?: OmicsProcessingResult["annotations"]["insdc_experiment_identifiers"]}): string | null => {
      const value = item.insdc_experiment_identifiers;
      if (Array.isArray(value)) {
        return typeof value[0] === "string" ? value[0] : null;
      } else {
        return typeof value === "string" ? value : null;
      }
    };

    /**
     * Returns a URL ready for use as the value of the `href` attribute of a link element.
     * 
     * Note: If `insdcExperimentIdentifier` is `null`, we set the URL to "#" so that the link is a
     *       valid HTML element, although clicking on it doesn't take the user anywhere. However,
     *       the way we use this function today, we don't even _render_ the link in that situation.
     */
    const makeInsdcHref = (insdcExperimentIdentifier: string | null): string => {
      if (typeof insdcExperimentIdentifier === "string") {
        return new URL(insdcExperimentIdentifier, BioprojectLinkBase).toString();
      } else {
        return "#";
      }
    };

    return {
      headers,
      items,
      BioprojectLinkBase,
      getFirstInsdcExperimentIdentifier,
      makeInsdcHref,
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
        v-if="typeof getFirstInsdcExperimentIdentifier(item) === 'string'"
        :href="makeInsdcHref(getFirstInsdcExperimentIdentifier(item))"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ getFirstInsdcExperimentIdentifier(item) }}
      </a>
    </template>
  </v-data-table>
</template>
