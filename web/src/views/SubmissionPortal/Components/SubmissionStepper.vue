<script lang="ts">
import {
  computed, defineComponent, reactive, toRef, watch, getCurrentInstance,
} from 'vue';
import VueRouter from 'vue-router';
import { incrementalSaveRecord } from '../store';

const StepperMap: Record<string | number, number | string> = {
  'Submission Home': 1,
  1: 'Submission Home',

  'Submission Context': 2,
  2: 'Submission Context',

  'Study Form': 3,
  3: 'Study Form',

  'Multiomics Form': 4,
  4: 'Multiomics Form',

  'Environment Package': 5,
  5: 'Environment Package',

  'Submission Sample Editor': 6,
  6: 'Submission Sample Editor',

  // 'Validate And Submit': 5,
  // 5: 'Validate And Submit',
};

export default defineComponent({
  setup() {
    const root = getCurrentInstance();

    const currentRoute = toRef(reactive(root?.proxy.$router as VueRouter), 'currentRoute');
    const step = computed(() => StepperMap[currentRoute.value.name || ''] || 0);

    const currentRouteName = computed(() => root?.proxy.$route.name);

    watch(currentRouteName, () => {
      if (root?.proxy.$route.params.id) {
        incrementalSaveRecord(root?.proxy.$route.params.id);
      }
    });

    function gotoStep(newstep: number) {
      const routeName = StepperMap[newstep];
      if (newstep < step.value && typeof routeName === 'string') {
        root?.proxy.$router.push({ name: routeName });
      }
    }

    return { step, gotoStep, StepperMap };
  },
});
</script>

<template>
  <v-stepper
    :value="step"
    class="mb-3 flex-shrink-0"
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
        Home
        <small>Begin or resume a submission.</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="2"
        :editable="2 < step"
        :complete="2 < step"
        @click="gotoStep(2)"
      >
        Submission Context
        <small>Input form</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="3"
        :editable="3 < step"
        :complete="3 < step"
        @click="gotoStep(3)"
      >
        Study Information
        <small>Input Form</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="4"
        :editable="4 < step"
        :complete="4 < step"
        @click="gotoStep(4)"
      >
        Multi-omics Data
        <small>Input Form</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="5"
        :editable="5 < step"
        :complete="5 < step"
        @click="gotoStep(5)"
      >
        Environment Package
        <small>Choose package type</small>
      </v-stepper-step>
      <v-divider />
      <v-stepper-step
        step="6"
        :editable="6 < step"
        :complete="6 < step"
        @click="gotoStep(6)"
      >
        Customize Metadata Export
        <small>DataHarmonizer sample validation</small>
      </v-stepper-step>
    </v-stepper-header>
  </v-stepper>
</template>
