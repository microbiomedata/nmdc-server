<script>
import { mapGetters } from 'vuex';
import { types } from '@/encoding';
import { fieldDisplayName } from '@/util';

import ConditionChips from '@/components/Presentation/ConditionChips.vue';
import FacetedSearch from '@/components/Presentation/FacetedSearch.vue';

import MatchList from './MatchList.vue';

export default {
  components: {
    ConditionChips,
    FacetedSearch,
    MatchList,
  },
  data: () => ({
    types,
  }),
  computed: {
    ...mapGetters(['type', 'conditions', 'primitiveFields']),
    typeFields() {
      return this.primitiveFields(this.type);
    },
  },
  methods: {
    fieldDisplayName,
  },
};
</script>

<template>
  <v-navigation-drawer
    app
    clipped
    permanent
    width="320"
  >
    <div class="ma-3">
      <div class="text-subtitle-2 primary--text">
        I am looking for...
      </div>
      <v-btn-toggle
        :value="type"
        mandatory
        dense
        class="my-3"
      >
        <template v-for="t in Object.keys(types)">
          <v-btn
            v-if="types[t].visible || type === t"
            :key="t"
            :value="t"
            :text="type !== t"
            :color="type === t ? 'primary' : 'inherit'"
            :class="{ 'white--text': type === t }"
            small
            @click="$store.dispatch('route', { name: 'Search', type: t, conditions })"
          >
            {{ types[t].heading }}
          </v-btn>
        </template>
      </v-btn-toggle>
      <div class="text-subtitle-2 primary--text">
        That match the following
      </div>
    </div>

    <ConditionChips
      :conditions="conditions"
      class="ma-3"
    >
      <template #menu="{ field, isOpen }">
        <div>
          <v-card-title class="pb-0">
            {{ fieldDisplayName(field) }}
          </v-card-title>
          <MatchList
            v-if="isOpen"
            :field="field"
          />
        </div>
      </template>
    </ConditionChips>

    <v-divider class="my-3" />

    <FacetedSearch
      :conditions="conditions"
      :type="type"
      :fields="typeFields"
    >
      <template #menu="{ field, isOpen }">
        <div>
          <v-card-title class="pb-0">
            {{ fieldDisplayName(field) }}
          </v-card-title>
          <MatchList
            v-if="isOpen"
            :field="field"
          />
        </div>
      </template>
    </FacetedSearch>
  </v-navigation-drawer>
</template>
