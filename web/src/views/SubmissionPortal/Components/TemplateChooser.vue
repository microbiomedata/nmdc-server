<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import { HARMONIZER_TEMPLATES } from '../harmonizerApi';
import { templateName } from '../store';

export default defineComponent({
  setup() {
    return {
      templateName,
      templates: Object.keys(HARMONIZER_TEMPLATES),
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
        :key="option"
        :value="option"
        :label="option"
      />
    </v-radio-group>
    <div class="d-flex">
      <v-btn
        color="gray"
        depressed
        :to="{ name: 'Study Form' }"
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
          params: { templateName },
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
