<script lang="ts">
// @ts-ignore
import {
  defineComponent,
  ref,
} from 'vue';
import Definitions from '@/definitions';
import {
    generateRecord,
    canEditSubmissionMetadata,
} from '../store';
import { useRouter } from 'vue-router';
import { ValidationResult } from 'vuetify/lib/composables/validation.mjs';

export default defineComponent({
  setup() {
    const isTestSubmission = ref(null as boolean | null);
    const piEmail = ref("")
    const studyName = ref("")
    const router = useRouter();
    const isFormValid = ref(false);

    async function createNewSubmission() {
      if (isTestSubmission.value != null) {
        const item = await generateRecord(isTestSubmission.value, studyName.value, piEmail.value);
        router?.push({ name: 'Submission Summary', params: { id: item.id } });
      }
    }

     function requiredRules(msg: string, otherRules: ((_v: string) => ValidationResult)[] = []) {
      return [
        (v: string) => !!v || msg,
        ...otherRules,
      ];
    }

    return {
      canEditSubmissionMetadata,
      requiredRules,
      createNewSubmission,
      piEmail,
      studyName,
      isTestSubmission,
      Definitions,
      isFormValid,
    };
  },
});
</script>

<template>
  <div>
    <v-container>
        <h1 class="text-h2">
            Study Information
        <submission-docs-link anchor="study" />
        </h1>
        <div class="text-h5">
            {{ "Input basic study information to get started with your submission. You may update the Study Name and Email later." }}
        </div>
        <v-form
            v-model="isFormValid"
            class="my-6 mb-10"
            style="max-width: 1000px;"
        >
            <div class="stack-md">
                <v-text-field
                    v-model="studyName"
                    :rules="requiredRules('Name is required',[
                        v => v.length > 6 || 'Study name too short',
                    ])"
                    validate-on-blur
                    label="Study Name *"
                    :hint="Definitions.studyName"
                    persistent-hint
                    variant="outlined"
                />
                <v-text-field
                    v-model="piEmail"
                    label="Email *"
                    :rules="requiredRules('E-mail is required',[
                        v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
                    ])"
                    :hint="Definitions.piEmail"
                    persistent-hint
                    type="email"
                    required
                    variant="outlined"
                />
                <v-radio-group
                v-model="isTestSubmission"
                row
                :rules="[v => (v === true || v === false) || 'You must select if this is a test submission.']"
                >
                    <template #label>
                        <span> Is this a test submission? * </span>
                        <v-tooltip right>
                            <template #activator="{ props }">
                                <v-icon
                                class="pl-2"
                                color="primary"
                                v-bind="props"
                                >
                                mdi-information
                                </v-icon>
                            </template>
                            <span>Test submissions should be used when at a workshop or doing a test, example, or training. These cannot be submitted.</span>
                        </v-tooltip>
                    </template>
                    <v-radio
                        label="Yes"
                        :value="true"
                    />
                    <v-radio
                        label="No"
                        :value="false"
                    />
                </v-radio-group>
            </div>
        </v-form>
        <div class="d-flex my-4">
            <v-btn
            color="gray"
            depressed
            :to="{ name: 'Submission Home' }"
            >
                <v-icon class="pl-1">
                    mdi-arrow-left-circle
                </v-icon>
                Go to Submission List
            </v-btn>
            <v-spacer />
            <v-btn
                color="primary"
                :disabled="!isFormValid"
                @click="createNewSubmission()"
            >
                Start Submission
            </v-btn>
        </div>
    </v-container>
  </div>
</template>
