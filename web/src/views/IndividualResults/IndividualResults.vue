<script>
import { mapGetters } from 'vuex';

import Sample from '@/components/Presentation/Sample.vue';
import Study from '@/components/Presentation/Study.vue';
import DataObject from '@/components/Presentation/DataObject.vue';
import Project from '@/components/Presentation/Project.vue';

import AttributeList from './AttributeList.vue';

export default {
  components: {
    AttributeList,
    DataObject,
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

  created() {
    this.$store.dispatch('refreshAll');
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
      <Study
        v-if="type === 'study'"
        :item="result"
      />
      <Sample
        v-if="type === 'biosample'"
        :item="result"
      />
      <Project
        v-if="type === 'project'"
        :item="result"
      />
      <DataObject
        v-if="type === 'data_object'"
        :item="result"
      />
      <AttributeList
        :type="type"
        :item="result"
        @selected="$router.push({
          name: 'Search',
          params: { type: $event.type },
          query: { conditions: $event.conditions },
        })"
      />
    </v-container>
  </v-main>
</template>
