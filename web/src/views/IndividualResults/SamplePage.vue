<script lang="ts">
import { defineComponent, ref, watchEffect } from 'vue';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import AttributeList from '@/components/Presentation/AttributeList.vue';
import ClickToCopyText from '@/components/Presentation/ClickToCopyText.vue';

import IndividualTitle from './IndividualTitle.vue';
import useRequest from '@/use/useRequest.ts';

export default defineComponent({
  name: 'SamplePage',

  components: {
    AppBanner,
    ClickToCopyText,
    AttributeList,
    IndividualTitle,
  },

  props: {
    id: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const biosample = ref<BiosampleSearchResult | null>(null);

    const getBiosampleRequest = useRequest();
    watchEffect(() => {
      getBiosampleRequest.request(async () => {
        biosample.value = await api.getBiosample(props.id)
      });
    });

    return {
      biosample,
      loading: getBiosampleRequest.loading,
    };
  },
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
        <router-link :to="{ name: 'Search' }">Home</router-link>
        <span class="mx-2">/</span>
        <ClickToCopyText>{{ biosample.id }}</ClickToCopyText>
      </div>
      <IndividualTitle :item="biosample" />
      <AttributeList
        type="biosample"
        :item="biosample"
      />
    </v-container>
  </v-main>
</template>
