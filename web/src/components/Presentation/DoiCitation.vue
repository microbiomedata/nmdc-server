<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';
// @ts-ignore
import Cite from 'citation-js';
import { DoiInfo } from '@/data/api';
import { urlify } from '@/data/utils';

const CITATION_OVERRIDES: Record<string, string> = {
  '10.46936/10.25585/60000017': 'Doktycz, M. (2020) BioScales - Defining plant gene function and its connection to ecosystem nitrogen and carbon cycling [Data set]. DOE Joint Genome Institute. https://doi.org/10.46936/10.25585/60000017',
};

export default defineComponent({
  props: {
    doi: {
      type: Object as PropType<DoiInfo>,
      required: true,
    },
  },

  setup(props) {
    const citation = computed(() => {
      if (CITATION_OVERRIDES[props.doi.info.DOI]) {
        return CITATION_OVERRIDES[props.doi.info.DOI];
      }
      const cite = new Cite(props.doi.info);
      const formatted = cite.format('bibliography', {
        format: 'text',
        template: 'apa',
        lang: 'en-US',
      });
      return urlify(formatted);
    });

    return {
      citation,
    };
  },
});
</script>

<template>
  <div>
    <div v-html="citation" />
    <div
      v-if="doi.provider"
      class="text-caption"
    >
      <span class="font-weight-medium">DOI Provider</span>: <span class="text-uppercase">{{ doi.provider }}</span>
    </div>
  </div>
</template>
