<script lang="ts">
import { computed, defineComponent } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES, getVariant } from '../harmonizerApi';
import { templateName, multiOmicsForm } from '../store';

export default defineComponent({
  setup() {
    const templateChoice = computed(() => {
      const checkBoxes = multiOmicsForm.omicsProcessingTypes;
      const template = HARMONIZER_TEMPLATES[templateName.value];
      try {
        const variant = getVariant(checkBoxes, template.variations, template.default);
        return `Using template "${variant}"`;
      } catch (err) {
        return `${err}.  Using ${template.default} instead.`;
      }
    });
    return {
      templateName,
      templateChoice,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
    };
  },
});
</script>

<template>
  <div>
    <div class="text-h2">
      Environment Package
    </div>
    <div class="text-h5">
      Choose environment package for your data.
    </div>
    <v-radio-group
      v-model="templateName"
      class="my-6"
    >
      <v-radio
        v-for="option in templates"
        :key="option[0]"
        :value="option[0]"
        :disabled="HARMONIZER_TEMPLATES[option[0]].status === 'disabled'"
        :label="option[0]"
      />
    </v-radio-group>
    <v-alert color="grey lighten-2">
      <p class="text-h5">
        DataHarmonizer Template
      </p>
      {{ templateChoice }}
    </v-alert>
    <div class="d-flex">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Multiomics Form' }"
      >
        <v-icon class="pr-1">
          mdi-arrow-left-circle
        </v-icon>
        Go to previous step
      </v-btn>
      <v-spacer />
      <v-btn
        color="primary"
        depressed
        :disabled="!templateName"
        :to="{
          name: 'Submission Sample Editor',
        }"
      >
        <v-icon class="pr-1">
          mdi-arrow-right-circle
        </v-icon>
        Go to next step
      </v-btn>
    </div>
  </div>
</template>
