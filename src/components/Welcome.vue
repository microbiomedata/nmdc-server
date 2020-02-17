<template>
  <v-card
    flat
    class="ma-3"
  >
    <v-container fluid>
      <v-row
        class="headline"
        justify="center"
      >
        Explore NMDC data
      </v-row>
      <v-row
        class="my-6"
        justify="center"
      >
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('type', 'study')"
        >
          Browse studies
        </v-btn>
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('type', 'project')"
        >
          Search by omics type
        </v-btn>
        <v-btn
          x-large
          color="primary"
          elevation="0"
          class="ma-4"
          @click="$emit('type', 'sample')"
        >
          Explore habitats
        </v-btn>
      </v-row>
    </v-container>
    <LocationMap
      :data="samples"
      @selected="addSelected($event)"
    />
    <v-container fluid>
      <v-row>
        <template
          v-for="(stat, index) in stats"
        >
          <v-divider
            v-if="index !== 0"
            :key="`${stat.label}-divider`"
            class="mx-4"
            vertical
          />
          <v-col :key="stat.label">
            <div class="headline text-center">
              {{ stat.value }}
            </div>
            <div class="title text-center">
              {{ stat.label }}
            </div>
          </v-col>
        </template>
      </v-row>
    </v-container>
  </v-card>
</template>
<script>
import LocationMap from './LocationMap.vue';
import { types } from '../encoding';

export default {
  components: {
    LocationMap,
  },
  props: {
    samples: {
      type: Array,
      default: () => [],
    },
    stats: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      types,
    };
  },
};
</script>
