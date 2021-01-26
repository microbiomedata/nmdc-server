<script lang="ts">
import { defineComponent } from '@vue/composition-api';

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

});
</script>

<template>
  <v-main>
    <v-container>
      <sample :item="result" />
      <attribute-list
        type="sample"
        :item="result"
        @selected="$store.dispatch('route', {
          name: 'Search',
          type: $event.type || type,
          conditions: $event.conditions,
        })"
      />
      <data-object-list
        :id="result.id"
        type="sample"
      />
    </v-container>
  </v-main>
</template>
