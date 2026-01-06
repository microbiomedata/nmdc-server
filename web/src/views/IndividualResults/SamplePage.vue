<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import AttributeList from '@/components/Presentation/AttributeList.vue';
import { downloadJson } from '@/utils';
import ClickToCopyText from '@/components/Presentation/ClickToCopyText.vue';

import IndividualTitle from './IndividualTitle.vue';
import useRequest from '@/use/useRequest.ts';

const props = defineProps<{
  id: string;
}>();

const biosample = ref<BiosampleSearchResult | null>(null);
const getBiosampleRequest = useRequest();
const loading = getBiosampleRequest.loading;
const sampleDownloadDialog = ref(false);
const sampleDownloadLoading = ref(false);
const errorDialog = ref(false);

async function downloadSampleData() {
  try {
    sampleDownloadDialog.value = false;
    sampleDownloadLoading.value = true;
    const data = await api.getBiosampleSource(props.id);
    downloadJson(data, `${props.id}.json`);
  } catch (error) {
    console.error('Failed to download study data:', error);
    errorDialog.value = true;
  } finally {
    sampleDownloadLoading.value = false;
  }
}

watchEffect(() => {
  getBiosampleRequest.request(async () => {
    biosample.value = await api.getBiosample(props.id);
  });
});
</script>

<template>
  <v-main>
    <AppBanner />
    <v-container v-if="loading">
      <v-skeleton-loader type="article" />
    </v-container>
    <v-container v-if="!loading && biosample !== null">
      <div class="text-caption mb-3">
        <router-link :to="{ name: 'Search' }">
          Home
        </router-link>
        <span class="mx-2">/</span>
        <ClickToCopyText>{{ biosample.id }}</ClickToCopyText>
      </div>
      <IndividualTitle :item="biosample" />
      <v-dialog
        v-model="sampleDownloadDialog"
        max-width="400"
      >
        <template #activator="{ props: dialogProps }">
          <v-btn
            v-bind="dialogProps"
            class="mb-8"
            color="primary"
            size="small"
          >
            <v-icon class="mr-2">
              mdi-download
            </v-icon>
            Download Sample Metadata
          </v-btn>
        </template>
        <DownloadDialog
          :loading="sampleDownloadLoading"
          @clicked="downloadSampleData"
        />
      </v-dialog>
      <v-snackbar
        v-model="sampleDownloadLoading"
        location="right bottom"
        timeout="-1"
      >
        <v-progress-circular
          indeterminate
          class="mr-3"
        />
        <span>
          Downloading sample metadata
        </span>
      </v-snackbar>
      <ErrorDialog
        v-model:show="errorDialog"
      />
      <AttributeList
        type="biosample"
        :item="biosample"
      />
    </v-container>
  </v-main>
</template>
