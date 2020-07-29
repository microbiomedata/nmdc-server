<script>
import { mapGetters } from 'vuex';

import Sample from '@/components/Presentation/Sample.vue';
import Study from '@/components/Presentation/Study.vue';
import Project from '@/components/Presentation/Project.vue';
import DataObjectList from '@/components/DataObjectsList.vue';

import AttributeList from './AttributeList.vue';

export default {
  components: {
    AttributeList,
    DataObjectList,
    Project,
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
};
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
      <project
        v-if="type === 'project'"
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
        v-if="[
          'project',
          'reads_qc',
          'metagenome_assembly',
          'metagenome_annotation',
          'metaproteomic_analysis',
        ].includes(type)"
        :id="result.id"
        :type="type"
      />
    </v-container>
  </v-main>
</template>
