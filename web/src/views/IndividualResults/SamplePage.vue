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

async function downloadSampleData() {
  const data = await api.getBiosampleSource(props.id);
  downloadJson(data, `${props.id}.json`);
}

watchEffect(() => {
  getBiosampleRequest.request(async () => {
    console.log('Fetching biosample', props.id);
    biosample.value = await api.getBiosample(props.id);
    console.log('Fetched biosample', biosample.value);
    console.log(getBiosampleRequest.loading.value);
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
      <v-btn
        class="mb-8"
        color="primary"
        size="small"
        @click="downloadSampleData"
      >
        <v-icon class="mr-2">
          mdi-download
        </v-icon>
        Download Sample Metadata
      </v-btn>
      <AttributeList
        type="biosample"
        :item="biosample"
      />
    </v-container>
  </v-main>
</template>
