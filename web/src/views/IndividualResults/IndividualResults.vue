<script>
import Vue from 'vue';
import { mapGetters } from 'vuex';

import Sample from '@/components/Presentation/Sample.vue';
import Study from '@/components/Presentation/Study.vue';
import OmicsProcessing from '@/components/Presentation/OmicsProcessing.vue';
import DataObjectList from '@/components/DataObjectsList.vue';

import AttributeList from './AttributeList.vue';

export default Vue.extend({
  components: {
    AttributeList,
    DataObjectList,
    OmicsProcessing,
    Sample,
    Study,
  },

  computed: {
    ...mapGetters(['typeResults', 'type']),

    result() {
      const list = this.typeResults(this.type);
      return list ? list[0] : null;
    },
  },
});
</script>

<template>
  <v-main>
    <v-container
      v-if="result"
      fluid
      style="background: white; height: 100%"
    >
      <study
        v-if="type === 'study'"
        :item="result"
      />
      <sample
        v-if="type === 'biosample'"
        :item="result"
      />
      <omics-processing
        v-if="type === 'omics_processing'"
        :item="result"
      />
      <attribute-list
        :type="type"
        :item="result"
        @selected="$store.dispatch('route', {
          name: 'Search',
          type: $event.type || type,
          conditions: $event.conditions,
        })"
      />
      <data-object-list
        :id="result.id"
        :type="type"
      />
    </v-container>
  </v-main>
</template>
