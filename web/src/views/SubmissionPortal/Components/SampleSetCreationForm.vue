<script setup lang="ts">
import { ref } from 'vue';
import Definitions from '@/definitions';
import { useRouter } from 'vue-router';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';
import PageTitle from '@/components/Presentation/PageTitle.vue';
import { useSubmissionStore } from '../store';

const store = useSubmissionStore();
const { createSubmissionSampleSet } = store;

const sampleSetName = ref('');
const isFormValid = ref(false);
const router = useRouter();

async function createNewSampleSet() {
  const item = await createSubmissionSampleSet(sampleSetName.value);
  if (item === null) {
    return;
  }
  router?.push({ name: 'Multiomics Form', params: { sampleSetId: item.id } });
}

function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[] = []) {
  return [
    (v: string) => !!v || msg,
    ...otherRules,
  ];
}
</script>

<template>
  <div>
    <v-container>
      <PageTitle
        title="Create New Sample Set"
        subtitle="Provide a title for your sample set to get started."
      />
      <v-form
        v-model="isFormValid"
        class="my-6 mb-10"
      >
        <div class="stack-md">
          <v-text-field
            v-model="sampleSetName"
            :rules="requiredRules('Name is required',[
              v => v.length > 6 || 'Sample set name too short',
            ])"
            validate-on-blur
            label="Sample Set Name"
            persistent-hint
            :hint="Definitions.sampleSetName"
            variant="outlined"
          />
        </div>
      </v-form>
      <div class="d-flex my-4">
        <v-btn
          color="gray"
          depressed
          :to="{ name: 'Submission Summary', params: { id: store.submission.record?.id } }"
        >
          <v-icon class="pr-1">
            mdi-arrow-left-circle
          </v-icon>
          Go to Submission Summary
        </v-btn>
        <v-spacer />
        <v-btn
          color="primary"
          :disabled="!isFormValid || store.sampleSet.requests.saving.loading"
          @click="createNewSampleSet()"
        >
          Start Sample Set
        </v-btn>
      </div>
    </v-container>
  </div>
</template>
