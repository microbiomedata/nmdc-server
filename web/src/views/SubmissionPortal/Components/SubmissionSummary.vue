<script lang="ts">
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';
import {
  computed,
  defineComponent,
  ref,
} from 'vue';
import {
  validForms,
  canEditSubmissionMetadata,
} from '../store';
import SubmissionPermissionBanner from './SubmissionPermissionBanner.vue';
import PageTitle from '@/components/Presentation/PageTitle.vue';

export default defineComponent({
  components: { SubmissionPermissionBanner },
  setup() {
    const textVal = ref('');

    const panels = ref([]);

    const studyFormContent = computed(() => {
      if (validForms.studyFormValid.length === 0) {
        return ['No changes needed.'];
      }
      return [...new Set(validForms.studyFormValid)];
    });

    const multiOmicsContent = computed(() => {
      if (validForms.multiOmicsFormValid.length === 0) {
        return ['No changes needed.'];
      }
      return [...new Set(validForms.multiOmicsFormValid)];
    });

    const harmonizerContent = computed(() => {
      if (validForms.templatesValid) {
        return 'Validate and correct any errors in your harmonizer data.';
      }
      return 'You must select one or more templates in the sample environment tab.';
    });

    return {
      validForms,
      NmdcSchema,
      textVal,
      panels,
      studyFormContent,
      multiOmicsContent,
      harmonizerContent,
      canEditSubmissionMetadata,
    };
  },
});
</script>

<template>
  <div>
    <v-container>
      <page-title
        title="Submission Summary"
        subtitle="Status and links to each portion of your submission."
      />
      <submission-permission-banner
        v-if="!canEditSubmissionMetadata()"
      />
      <v-expansion-panels
        model="panels"
        multiple
      >
        <v-expansion-panel>
          <v-expansion-panel-title disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Study Form Status
              </div>
              <v-btn
                color="primary"
                depressed
                :to="{ name: 'Study Form' }"
              >
                Go to Study Form
                <v-icon class="pl-1">
                  mdi-arrow-right-circle
                </v-icon>
              </v-btn>
            </div>
            <template #actions>
              <v-icon
                :color="validForms.studyFormValid.length === 0 ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.studyFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-list>
              <v-list-item
                v-for="(item, i) in studyFormContent"
                :key="i"
                :value="item"
                prepend-icon="mdi-circle-small"
              >
                {{ item }}
              </v-list-item>
            </v-list>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Multi-Omics Form Status
              </div>
              <v-btn
                color="primary"
                depressed
                :to="{ name: 'Multiomics Form' }"
              >
                Go to Multiomics Form
                <v-icon class="pl-1">
                  mdi-arrow-right-circle
                </v-icon>
              </v-btn>
            </div>
            <template #actions>
              <v-icon
                :color="validForms.multiOmicsFormValid.length === 0 ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.multiOmicsFormValid.length === 0 ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-list>
              <v-list-item
                v-for="(item, i) in multiOmicsContent"
                :key="i"
                :value="item"
                prepend-icon="mdi-circle-small"
              >
                {{ item }}
              </v-list-item>
            </v-list>
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Sample Environment/Template status
              </div>
              <v-btn
                color="primary"
                depressed
                :to="{ name: 'Sample Environment' }"
              >
                Go to Sample Environment
                <v-icon class="pl-1">
                  mdi-arrow-right-circle
                </v-icon>
              </v-btn>
            </div>
            <template #actions>
              <v-icon
                :color="validForms.templatesValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.templatesValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            {{ validForms.templatesValid ? 'No changes needed.' : 'You must select one or more templates.' }}
          </v-expansion-panel-text>
        </v-expansion-panel>
        <v-expansion-panel>
          <v-expansion-panel-title disable-icon-rotate>
            <div class="my-4">
              <div class="text-h5">
                Sample Metadata Status
              </div>
              <v-btn
                color="primary"
                depressed
                :to="{ name: 'Submission Sample Editor' }"
              >
                Go to Sample Metadata
                <v-icon class="pl-1">
                  mdi-arrow-right-circle
                </v-icon>
              </v-btn>
            </div>
            <template #actions>
              <v-icon
                :color="validForms.harmonizerValid ? 'green' : 'red'"
                :size="32"
              >
                {{ validForms.harmonizerValid ? 'mdi-check' : 'mdi-close-circle' }}
              </v-icon>
            </template>
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            {{ harmonizerContent }}
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
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
      </div>
    </v-container>
  </div>
</template>
