<script lang="ts">
import { defineComponent, ref, watchEffect } from '@vue/composition-api';
import { api, BiosampleSearchResult } from '@/data/api';
import AppBanner from '@/components/AppBanner.vue';
import AttributeList from '@/components/Presentation/AttributeList.vue';

import IndividualTitle from './IndividualTitle.vue';

export default defineComponent({
  name: 'SamplePage',

  components: {
    AppBanner,
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
    const result = ref({} as BiosampleSearchResult);

    watchEffect(() => {
      api.getBiosample(props.id).then((b) => { result.value = b; });
    });

    return { result };
  },
});
</script>

<template>
  <v-main v-if="result.id">
    <AppBanner />
    <v-container fluid>
      <IndividualTitle :item="result" />
      <AttributeList
        type="biosample"
        :item="result"
      />
    </v-container>
  </v-main>
</template>
