<script setup lang="ts">
import {
  computed,
  provide,
  useTemplateRef,
  watch,
} from 'vue';
import { stateRefs } from '@/store';
import AppBanner from '@/components/AppBanner.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IntroBlurb from '@/views/SubmissionPortal/Components/IntroBlurb.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';
import LoginPrompt from '@/views/SubmissionPortal/Components/LoginPrompt.vue';
import { useSubmissionStore } from './store';
import { AppBannerHeightKey } from '@/views/SubmissionPortal/types.ts';

const { id, sampleSetId } = defineProps<{
  id?: string,
  sampleSetId?: string,
}>();

const store = useSubmissionStore();

watch(() => id, (nextId) => {
  if (nextId !== undefined) {
    if (store.submission.record?.id !== nextId) {
      void store.loadSubmission(nextId);
    }
  } else {
    store.submission.requests.loading.reset();
  }
}, { immediate: true });

watch(() => sampleSetId, (nextSampleSetId) => {
  if (nextSampleSetId !== undefined) {
    if (store.sampleSet.record?.id !== nextSampleSetId) {
      void store.loadSampleSet(nextSampleSetId);
    }
  } else {
    store.sampleSet.requests.loading.reset();
  }
}, { immediate: true });

const submissionLoading = computed(() => store.submission.requests.loading.loading);
const sampleSetLoading = computed(() => store.sampleSet.requests.loading.loading);

const submissionReady = computed(() => (
  id === undefined || store.submission.record?.id === id
));
const submissionError = computed(() => store.submission.requests.loading.error);

const color = 'primary';
const density = 'comfortable';
const styleDefaults = {
  VBtn: {
    variant: "flat",
  },
  VBtnGrey: {
    variant: "flat",
  },
  VCombobox: {
    density,
    color,
  },
  VCheckbox: {
    density,
    color,
  },
  VFileInput: {
    density,
    color,
  },
  VRadio: {
    density,
    color,
  },
  VRadioGroup: {
    density,
    color,
  },
  VSelect: {
    density,
    color,
  },
  VTextField: {
    density,
    color,
  },
  VTextarea: {
    density,
    color,
  },
}

// Get the height of the app banner to provide to child components
const appBanner = useTemplateRef<InstanceType<typeof AppBanner>>("appBanner");
const appBannerHeight = computed(() => appBanner.value?.height || 0);
provide(AppBannerHeightKey, appBannerHeight);
</script>

<template>
  <v-defaults-provider :defaults="styleDefaults">
    <v-main class="d-flex flex-column">
      <AppBanner ref="appBanner" />
      <div class="position-relative">
        <v-progress-linear
          :active="submissionLoading || sampleSetLoading"
          absolute
          indeterminate
          color="primary"
        />
        <v-container
          v-if="!stateRefs.user.value && !submissionLoading"
        >
          <v-container class="mt-4 ">
            <v-row>
              <v-col class="pb-0">
                <TitleBanner />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <LoginPrompt />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <IconBar />
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <IntroBlurb />
              </v-col>
            </v-row>
          </v-container>
        </v-container>
        <div v-else-if="submissionError">
          <v-container>
            <v-alert type="error">
              <div class="text-h6">
                Error loading submission {{ id }}
              </div>
              {{ submissionError }}
            </v-alert>
          </v-container>
        </div>
        <router-view v-else-if="submissionReady" />
      </div>
    </v-main>
  </v-defaults-provider>
</template>
