<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES, useHarmonizerApi } from './harmonizerApi';

export default defineComponent({
  setup() {
    const iframeElement = ref();
    const harmonizerApi = useHarmonizerApi(iframeElement);

    function setupTemplate(templateName: keyof typeof HARMONIZER_TEMPLATES) {
      harmonizerApi.setupTemplate(HARMONIZER_TEMPLATES[templateName].folder);
    }

    return {
      iframeElement,
      harmonizerApi,
      templates: Object.keys(HARMONIZER_TEMPLATES),
      /* methods */
      setupTemplate,
    };
  },
});
</script>

<template>
  <v-main style="overflow-y: hidden;">
    <div class="d-flex align-center justify-center px-4 py-2">
      <v-spacer />
      <v-btn
        color="primary"
        class="mx-2"
        @click="harmonizerApi.validate"
      >
        Validate
      </v-btn>
      <v-autocomplete
        :items="templates"
        label="Choose Schema Template"
        class="shrink"
        outlined
        dense
        hide-details
        @input="setupTemplate"
      />
    </div>
    <iframe
      ref="iframeElement"
      title="Data Harmonizer"
      width="100%"
      height="100%"
      src="/data-harmonizer/main.html"
    />
  </v-main>
</template>
