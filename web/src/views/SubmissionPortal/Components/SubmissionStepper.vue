<script lang="ts">
import {
  computed, defineComponent, reactive, toRef, getCurrentInstance,
} from 'vue';
import VueRouter from 'vue-router';

const StepperMap: Record<string | number, number | string> = {
  'Submission Home': 1,
  1: 'Submission Home',

  'Study Form': 2,
  2: 'Study Form',

  'Multiomics Form': 3,
  3: 'Multiomics Form',

  'Sample Environment': 4,
  4: 'Sample Environment',

  'Submission Sample Editor': 5,
  5: 'Submission Sample Editor',

  // 'Validate And Submit': 5,
  // 5: 'Validate And Submit',
};

export default defineComponent({
  setup() {
    const root = getCurrentInstance();
    const currentRoute = toRef(reactive(root?.proxy.$router as VueRouter), 'currentRoute');
    const step = computed(() => {
      const mappedStep = StepperMap[currentRoute.value.name || ''];
      return typeof mappedStep === 'number' ? mappedStep : 0;
    });

    function gotoStep(newstep: number) {
      const routeName = StepperMap[newstep];
      if (newstep < step.value && typeof routeName === 'string' && root?.proxy) {
        root.proxy.$router.push({ name: routeName as any });
      }
    }

    return { step, gotoStep, StepperMap };
  },
});
</script>

<template>
  <v-stepper
    :model-value="step"
    class="mb-3 flex-shrink-0"
    alt-labels
  >
    <v-stepper-header>
      <v-stepper-item
        :value="1"
        :complete="1 < step"
        :editable="1 < step"
        title="Home"
        subtitle="Begin or resume a submission."
        @click="gotoStep(1)"
      />
      <v-divider />
      <v-stepper-item
        :value="2"
        :complete="2 < step"
        :editable="2 < step"
        title="Study Information"
        subtitle="Input Form"
        @click="gotoStep(2)"
      />
      <v-divider />
      <v-stepper-item
        :value="3"
        :complete="3 < step"
        :editable="3 < step"
        title="Multi-omics Data"
        subtitle="Input Form"
        @click="gotoStep(3)"
      />
      <v-divider />
      <v-stepper-item
        :value="4"
        :complete="4 < step"
        :editable="4 < step"
        title="Sample Environment"
        subtitle="Choose MIxS Extension"
        @click="gotoStep(4)"
      />
      <v-divider />
      <v-stepper-item
        :value="5"
        :complete="5 < step"
        :editable="5 < step"
        title="Customize Metadata Export"
        subtitle="DataHarmonizer sample validation"
        @click="gotoStep(5)"
      />
    </v-stepper-header>
  </v-stepper>
</template>
