<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import { downloadJson } from '@/utils';
// @ts-ignore
import { formatBiosampleDepth } from '@/util';

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

async function downloadSampleMetadata() {
  try {
    sampleDownloadDialog.value = false;
    sampleDownloadLoading.value = true;
    const data = await api.getBiosampleSource(props.id);
    downloadJson(data, `${props.id}.json`);
  } catch (error) {
    console.error('Failed to download sample metadata:', error);
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
      <BreadcrumbList
        :items="[
          { text: 'Data Portal Home', to: { name: 'Search' } },
          { text: biosample.id, copyable: true }
        ]"
      />
      <IndividualTitle :item="biosample">
        <template #subtitle>
          <div
            v-if="biosample.description"
            class="mb-2"
          >
            {{ biosample.description }}
          </div>
          <v-dialog
            v-model="sampleDownloadDialog"
            max-width="400"
          >
            <template #activator="{ props: dialogProps }">
              <v-btn
                v-bind="dialogProps"
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
              @clicked="downloadSampleMetadata"
            />
          </v-dialog>
        </template>
      </IndividualTitle>
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
      <v-card variant="outlined">
        <LabelValueTable
          :rows="[
            { label: 'Sample ID', value: biosample.id, iconString: 'mdi-barcode' },
            { label: 'Sample Name', value: biosample.name, iconString: 'mdi-text-box' },
            { label: 'Study ID', value: biosample.study_id, iconString: 'mdi-dna' },
            // TODO: add study_name to biosample model
            { label: 'Study Name', value: biosample.study_name, iconString: 'mdi-dna' },
            { label: 'Collection Date', value: biosample.collection_date, iconString: 'mdi-calendar' },
            { label: 'Location', value: biosample.annotations.geo_loc_name as string, iconString: 'mdi-map-marker' },
            { label: 'Latitude', value: biosample.latitude, iconString: 'mdi-map-marker-radius' },
            { label: 'Longitude', value: biosample.longitude, iconString: 'mdi-map-marker-radius' },
            { label: 'Depth', value: formatBiosampleDepth(biosample.annotations?.depth as object | null, biosample.depth as number | null), iconString: 'mdi-arrow-down-bold-circle-outline' },
            { label: 'Ecosystem', value: biosample.ecosystem, iconString: 'mdi-leaf' },
            { label: 'Ecosystem Category', value: biosample.ecosystem_category, iconString: 'mdi-leaf' },
            { label: 'Ecosystem Type', value: biosample.ecosystem_type, iconString: 'mdi-leaf' },
            { label: 'Ecosystem Subtype', value: biosample.ecosystem_subtype, iconString: 'mdi-leaf' },
            { label: 'Specific Ecosystem', value: biosample.specific_ecosystem, iconString: 'mdi-leaf' },
            { label: 'Broad Scale Environment', value: biosample.env_broad_scale, iconString: 'mdi-earth' },
            { label: 'Local Scale Environment', value: biosample.env_local_scale, iconString: 'mdi-earth' },
            { label: 'Environmental Medium', value: biosample.env_medium, iconString: 'mdi-earth' },
          ]"
        />
      </v-card>
    </v-container>
  </v-main>
</template>
