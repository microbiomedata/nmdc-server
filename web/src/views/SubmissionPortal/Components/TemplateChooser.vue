<script lang="ts">
import { defineComponent, computed } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import { templateChoice, templateChoiceDisabled, packageName } from '../store';

export default defineComponent({
  setup() {
    const disableOptionsWithoutVariations = computed(
      () => templateChoice.value.includes('jgi') || templateChoice.value.includes('emsl'),
    );
    return {
      packageName,
      templateChoice,
      HARMONIZER_TEMPLATES,
      templates: Object.entries(HARMONIZER_TEMPLATES),
      templateChoiceDisabled,
      disableOptionsWithoutVariations,
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
      v-model="packageName"
      class="my-6"
    >
      <v-radio
        v-for="option in templates.filter((v) => v[1].status !== 'disabled')"
        :key="option[0]"
        :value="option[0]"
        :disabled="templateChoiceDisabled || (disableOptionsWithoutVariations && !option[1].variations.length)"
        :label="option[0]"
      />
      <p class="grey--text text--darken-1 my-5">
        Under development
      </p>
      <v-radio
        v-for="option in templates.filter((v) => v[1].status === 'disabled')"
        :key="option[0]"
        :value="option[0]"
        :disabled="true"
        :label="option[0]"
      />
    </v-radio-group>
    <v-alert
      v-if="!templateChoiceDisabled"
      color="grey lighten-2"
    >
      <p class="text-h5">
        DataHarmonizer Template Choice
      </p>
      Your DataHarmonizer template is "{{ templateChoice }}".
      <span v-if="disableOptionsWithoutVariations">
        Because you have chosen data types specific to processing institutions,
        only packages with matching institution template variations are enabled.
      </span>
    </v-alert>
    <v-alert
      v-else
      type="warning"
    >
      <p class="text-h5">
        Template choice disabled
      </p>
      Your DataHarmonizer template is "{{ templateChoice }}".
      Template cannot be changed when there are already metadata rows in step 5.
      To change the template, return to step 5 and remove all data.
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
        :disabled="!packageName"
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
