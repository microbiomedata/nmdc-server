<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import {
  studyForm, multiOmicsForm, templateName, sampleData,
} from '../store';

export default defineComponent({
  setup() {
    const payload = computed(() => {
      const value = JSON.stringify({
        template: templateName.value,
        studyForm,
        multiOmicsForm,
        sampleData: `{ ${sampleData.value.length} samples }`,
      }, null, 2);
      return value;
    });

    return { payload };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Submit
    </div>
    <div class="text-h5">
      Preview of the data submission
    </div>
    <v-card
      class="pa-3"
      outlined
    >
      <pre style="font-size: 14px">{{ payload }}</pre>
    </v-card>
  </div>
</template>
