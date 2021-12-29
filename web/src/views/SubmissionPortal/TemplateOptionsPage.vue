<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from './harmonizerApi';

export default defineComponent({
  setup() {
    const templateName = ref(null as null | keyof typeof HARMONIZER_TEMPLATES);

    return {
      templateName,
      templates: Object.keys(HARMONIZER_TEMPLATES),
    };
  },
});
</script>

<template>
  <v-container>
    <div class="text-h2">
      Environment Package
    </div>
    <div class="text-h5">
      Choose environment package for your data.
    </div>
    <v-radio-group
      v-model="templateName"
    >
      <v-radio
        v-for="option in templates"
        :key="option"
        :value="option"
        :label="option"
      />
    </v-radio-group>
    <div class="d-flex">
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :disabled="!templateName"
        :to="{
          name: 'Submission Sample Editor',
          params: { templateName },
        }"
      >
        Go to next step
      </v-btn>
    </div>
  </v-container>
</template>
