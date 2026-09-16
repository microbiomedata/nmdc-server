<script setup lang="ts">
import { computed, ref, watchEffect } from 'vue';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import { downloadJson, formatEnvItem, formatSlotLabel, formatStringOrList, getEnvUrl, getIdentifierImage } from '@/utils';
// @ts-ignore
import { formatBiosampleDepth } from '@/util';

import IndividualTitle from './IndividualTitle.vue';
import useRequest from '@/use/useRequest.ts';
import { BadgeKey } from '@/components/Presentation/MetadataBadge.vue';
import { LabelValuePair } from '@/components/Presentation/LabelValueTable.vue';
import moment from 'moment';

const props = defineProps<{
  id: string;
}>();

const biosample = ref<BiosampleSearchResult | null>(null);
const getBiosampleRequest = useRequest();
const loading = getBiosampleRequest.loading;
const sampleDownloadDialog = ref(false);
const sampleDownloadLoading = ref(false);
const errorDialog = ref(false);
const EXCLUDED_ANNOTATION_FIELDS = [
  'type',
  'analysis_type',
  'samp_name',
  'geo_loc_name',
  'lat_lon',
  'depth',
  'biosample_categories',
];

const metadataRows = computed(() => {
  if (!biosample.value) {
    return [];
  }

  const visibleRows = [
    { label: 'Sample ID', value: biosample.value.id, iconString: 'mdi-test-tube' },
    { label: 'Sample Name', value: biosample.value.name, iconString: 'mdi-test-tube' },
    { label: 'Study ID', value: biosample.value.study_id, iconString: 'mdi-book-outline', href: biosample.value.study_id ? `/details/study/${biosample.value.study_id}` : undefined },
    { label: 'Collection Date', value: moment(biosample.value.collection_date).format('YYYY-MM-DD, HH:mm'), iconString: 'mdi-calendar' },
    { label: 'Location', value: biosample.value.annotations.geo_loc_name as string, iconString: 'mdi-earth' },
    { label: 'Latitude', value: biosample.value.latitude, iconString: 'mdi-map-marker-radius' },
    { label: 'Longitude', value: biosample.value.longitude, iconString: 'mdi-map-marker-radius' },
    { label: 'Depth', value: formatBiosampleDepth(biosample.value.annotations?.depth as object | null, biosample.value.depth as number | null), iconString: 'mdi-tape-measure' },
    { label: 'Ecosystem', value: biosample.value.ecosystem, iconString: 'mdi-pine-tree' },
    { label: 'Ecosystem Category', value: biosample.value.ecosystem_category, iconString: 'mdi-pine-tree' },
    { label: 'Ecosystem Type', value: biosample.value.ecosystem_type, iconString: 'mdi-pine-tree' },
    { label: 'Ecosystem Subtype', value: biosample.value.ecosystem_subtype, iconString: 'mdi-pine-tree' },
    { label: 'Specific Ecosystem', value: biosample.value.specific_ecosystem, iconString: 'mdi-pine-tree' },
    { label: 'Broad Scale Environment', value: formatEnvItem(biosample.value.env_broad_scale), iconString: 'mdi-leaf', href: biosample.value.env_broad_scale ? getEnvUrl(biosample.value.env_broad_scale.id) : undefined },
    { label: 'Local Scale Environment', value: formatEnvItem(biosample.value.env_local_scale), iconString: 'mdi-leaf', href: biosample.value.env_local_scale ? getEnvUrl(biosample.value.env_local_scale.id) : undefined },
    { label: 'Environmental Medium', value: formatEnvItem(biosample.value.env_medium), iconString: 'mdi-leaf', href: biosample.value.env_medium ? getEnvUrl(biosample.value.env_medium.id) : undefined },
    { label: 'Biosample Categories', value: formatStringOrList(biosample.value.annotations?.biosample_categories), iconString: 'mdi-tag-multiple' },
  ];

  return visibleRows;
});

const metadataHiddenRows = computed(() => {
  if (!biosample.value) {
    return [];
  }

  const hiddenRows = Object.keys(biosample.value.annotations).filter((field) => {
    return !EXCLUDED_ANNOTATION_FIELDS.includes(field);
  }).map((field) => {
    return { label: formatSlotLabel(field), value: biosample.value?.annotations[field], iconString: 'mdi-code-braces' };
  });

  return hiddenRows as LabelValuePair[];
});

const alternateIdentifiers = computed(() => {
  if (biosample.value) {
    return biosample.value.alternate_identifiers.map((id) => {
      return { name: id, target: `https://identifiers.org/${id}`, image: getIdentifierImage(id) };
    });
  }

  return [];
});

const relatedBiosamples = computed(() => {
  const relatedBiosampleIds = new Set();
  const relatedBiosampleInfo: any[] | Set<unknown> = [];
  if (biosample.value?.omics_processing.length) {
    biosample.value.omics_processing.forEach((omicsProcessing: any) => {
      if (omicsProcessing.biosample_inputs) {
        omicsProcessing.biosample_inputs.forEach((biosampleInput: BiosampleSearchResult) => {
          if (biosampleInput.id && biosampleInput.id !== biosample.value?.id) {
            if (!relatedBiosampleIds.has(biosampleInput.id)) {
              relatedBiosampleInfo.push({ id: biosampleInput.id, name: biosampleInput.name });
              relatedBiosampleIds.add(biosampleInput.id);
            }
          }
        });
      }
    });
  }
  return relatedBiosampleInfo;
});

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
    <ResponsiveContainer v-if="loading">
      <v-skeleton-loader type="article" />
    </ResponsiveContainer>
    <ResponsiveContainer v-if="!loading && biosample">
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
        </template>
        <template #actions>
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
      <v-row>
        <v-col
          xl="6" 
          lg="12"
          md="12"
          sm="12"
          xs="12"
        >
          <PageSection heading="Metadata">
            <v-card variant="outlined">
              <LabelValueTable
                :rows="[...metadataRows, ...metadataHiddenRows]"
              />
            </v-card>
          </PageSection>
        </v-col>
        <v-col
          xl="6" 
          lg="12"
          md="12"
          sm="12"
          xs="12"
        >
          <PageSection heading="Metadata Quality">
            <v-card
              v-if="biosample.badges?.length > 0"
              class="pa-4" 
              variant="outlined"
            >
              <v-row>
                <v-col
                  v-for="badge in biosample.badges"
                  :key="badge"
                  class="text-center"
                >
                  <MetadataBadge
                    :badge="badge as BadgeKey"
                  />
                </v-col>
              </v-row>
            </v-card>
            <div v-else>
              This sample has not earned any metadata quality badges.
            </div>
          </PageSection>
          <PageSection heading="Alternate Identifiers">
            <div
              v-if="alternateIdentifiers?.length > 0"
              class="d-flex flex-column ga-2 align-center"
            >
              <v-card
                v-for="identifier in alternateIdentifiers"
                :key="identifier.name"
                class="w-100"
                variant="outlined"
                :href="identifier.target"
                target="_blank"
                rel="noopener noreferrer"
              >
                <div class="d-flex align-center pa-2 ga-2">
                  <img
                    v-if="identifier.image"
                    :src="identifier.image"
                    width="160px"
                    class="pr-2"
                    alt="Logo"
                  >
                  <v-icon
                    v-else
                    class="mr-4"
                    color="grey-darken-4"
                    size="small"
                  >
                    mdi-link
                  </v-icon>
                  <span class="flex-fill">
                    {{ identifier.name }}
                  </span>
                  <v-icon
                    class="mr-2"
                    size="small"
                  >
                    mdi-open-in-new
                  </v-icon>
                </div>
              </v-card>
            </div>
            <div v-else>
              No alternate identifiers available for this sample.
            </div>
          </PageSection>
          <PageSection
            v-if="relatedBiosamples?.length > 0"
            heading="Related Biosamples"
          >
            <div
              class="d-flex flex-column ga-2 align-center"
            >
              <v-card
                v-for="relatedSample in relatedBiosamples"
                :key="relatedSample.id"
                class="w-100"
                variant="outlined"
                :href="'/details/sample/' + relatedSample.id"
              >
                <div class="d-flex align-center pa-2 ga-2">
                  <v-icon
                    class="mr-4"
                    color="grey-darken-4"
                    size="small"
                  >
                    mdi-test-tube
                  </v-icon>
                  <span class="flex-fill">
                    {{ relatedSample.name }}
                  </span>
                </div>
              </v-card>
            </div>
          </PageSection>
        </v-col>
      </v-row>
    </ResponsiveContainer>
  </v-main>
</template>
