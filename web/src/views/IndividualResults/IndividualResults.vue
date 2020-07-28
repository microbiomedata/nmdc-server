<script>
import { mapGetters } from 'vuex';

import Sample from '@/components/Presentation/Sample.vue';
import Study from '@/components/Presentation/Study.vue';
import Project from '@/components/Presentation/Project.vue';

import AttributeList from './AttributeList.vue';

export default {
  components: {
    AttributeList,
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
      <AttributeList
        :type="type"
        :item="result"
        @selected="$store.dispatch('route', {
          name: 'Search',
          type,
          conditions: $event.conditions,
        })"
      />
    </v-container>
  </v-main>
</template>
