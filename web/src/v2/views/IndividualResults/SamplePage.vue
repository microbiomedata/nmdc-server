<script lang="ts">
import { defineComponent, ref, watchEffect } from '@vue/composition-api';
import { api, BiosampleSearchResult } from '@/data/api';

import DataObjectList from '@/v2/components/DataObjectsList.vue';
import AttributeList from '@/v2/components/AttributeList.vue';

import IndividualTitle from './IndividualTitle.vue';

export default defineComponent({
  name: 'SamplePageV2',

  components: {
    AttributeList,
    DataObjectList,
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
    <v-container fluid>
      <IndividualTitle :item="result" />
      <AttributeList
        type="biosample"
        :item="result"
      />
      <DataObjectList
        :id="result.id"
        type="biosample"
      />
    </v-container>
  </v-main>
</template>
