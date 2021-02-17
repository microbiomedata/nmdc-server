<script>
import Vue from 'vue';
import LocationMap from './LocationMap.vue';

export default Vue.extend({
  components: {
    LocationMap,
  },
  props: {
    stats: {
      type: Array,
      default: () => [],
    },
  },
});
</script>

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
        National Microbiome Data Collaborative
      </v-row>
      <v-row
        class="my-6"
        justify="center"
      >
        <v-btn
          x-large
          color="cyan darken-1"
          dark
          elevation="0"
          class="ma-4"
          :to="{ name: 'V2Search' }"
        >
          Search NMDC Data
        </v-btn>
      </v-row>
    </v-container>
    <LocationMap />
    <v-container fluid>
      <template
        v-for="(statsLine, i) in stats"
      >
        <v-row
          :key="i"
        >
          <template
            v-for="stat in statsLine"
          >
            <v-col
              v-if="stat.value !== 0"
              :key="stat.label"
            >
              <v-card
                height="150"
                outlined
              >
                <v-container
                  fluid
                  style="height: 100%"
                >
                  <v-row
                    align="center"
                    align-content="center"
                    style="height: 100%"
                  >
                    <v-col
                      cols="12"
                      class="display-1 text-center py-1"
                    >
                      {{ stat.value }}
                    </v-col>
                    <v-col
                      cols="12"
                      class="title text-center py-1"
                    >
                      {{ stat.label }}
                    </v-col>
                  </v-row>
                </v-container>
              </v-card>
            </v-col>
          </template>
        </v-row>
      </template>
    </v-container>
  </v-card>
</template>
