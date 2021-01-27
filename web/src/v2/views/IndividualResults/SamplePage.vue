<script lang="ts">
import { defineComponent, ref } from '@vue/composition-api';
import { api, BiosampleSearchResult } from '@/data/api';
import Sample from '@/components/Presentation/Sample.vue';
import DataObjectList from '@/components/DataObjectsList.vue';
import AttributeList from '@/views/IndividualResults/AttributeList.vue';

export default defineComponent({
  name: 'SamplePageV2',

  components: {
    AttributeList,
    DataObjectList,
    Sample,
  },

  props: {
    id: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const result = ref({} as BiosampleSearchResult);
    api.getBiosample(props.id).then((b) => { result.value = b; });

    return { result };
  },
});
</script>

<template>
  <v-main v-if="result.id">
    <v-container fluid>
      <sample :item="result" />
      <attribute-list
        type="sample"
        :item="result"
      />
      <data-object-list
        :id="result.id"
        type="biosample"
      />
    </v-container>
  </v-main>
</template>
