<script setup lang="ts">
import { ref, watchEffect } from 'vue';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import AttributeList from '@/components/Presentation/AttributeList.vue';
import { downloadJson } from '@/utils';

import IndividualTitle from './IndividualTitle.vue';

const props = defineProps<{
  id: string;
}>();

const result = ref({} as BiosampleSearchResult);

async function downloadSampleData() {
  const data = await api.getMongoBiosample(props.id);
  downloadJson(data, `${props.id}.json`);
}

watchEffect(() => {
  api.getBiosample(props.id).then((b) => { 
    result.value = b; 
  });
});
</script>

<template>
  <v-main v-if="result.id">
    <AppBanner />
    <v-container fluid>
      <div class="d-flex align-center">
        <IndividualTitle :item="result" />
        <JsonDownload 
          :json="result" 
          :filename="`${result.id}.json`"
        />
        <v-btn 
          color="primary" 
          @click="downloadSampleData"
        >
          <v-icon class="mr-2">
            mdi-download
          </v-icon>
          Download Sample Data
        </v-btn>
      </div>
      <AttributeList
        type="biosample"
        :item="result"
      />
    </v-container>
  </v-main>
</template>
