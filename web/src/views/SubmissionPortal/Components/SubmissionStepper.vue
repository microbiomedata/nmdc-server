<script lang="ts">
import {
  computed, defineComponent, reactive, toRef,
} from '@vue/composition-api';

const StepperMap: Record<string | number, number | string> = {
  'Study Form': 1,
  1: 'Study Form',

  'Multiomics Form': 2,
  2: 'Multiomics Form',

  'Environment Package': 3,
  3: 'Environment Package',

  'Submission Sample Editor': 4,
  4: 'Submission Sample Editor',

  'Validate And Submit': 5,
  5: 'Validate And Submit',
};

export default defineComponent({
  setup(props, { root }) {
    const currentRoute = toRef(reactive(root.$router), 'currentRoute');
    const step = computed(() => StepperMap[currentRoute.value.name || ''] || 0);

    function gotoStep(newstep: number) {
      const routeName = StepperMap[newstep];
      if (newstep < step.value && typeof routeName === 'string') {
        root.$router.push({ name: routeName });
      }
    }

    return { step, gotoStep, StepperMap };
  },
});
</script>

<template>
  <v-stepper
    :value="step"
    class="mb-3"
    outlined
    tile
    dark
  >
    <v-stepper-header>
      <v-stepper-step
        step="1"
        :editable="1 < step"
        :complete="1 < step"
        @click="gotoStep(1)"
      >
        Study Information
        <small>Input Form</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="2"
        :editable="2 < step"
        :complete="2 < step"
        @click="gotoStep(2)"
      >
        Multiomics Data
        <small>Input Form</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="3"
        :editable="3 < step"
        :complete="3 < step"
        @click="gotoStep(3)"
      >
        Environment Package
        <small>Choose package type</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="4"
        :editable="4 < step"
        :complete="4 < step"
        @click="gotoStep(4)"
      >
        Customize Metadata Export
        <small>DataHarmonizer sample validation</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="5"
        :editable="5 < step"
        :complete="5 < step"
        @click="gotoStep(5)"
      >
        Validate and Submit
      </v-stepper-step>
    </v-stepper-header>
  </v-stepper>
</template>
