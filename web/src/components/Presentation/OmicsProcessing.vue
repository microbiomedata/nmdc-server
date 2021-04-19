<script>
export default {
  props: {
    item: {
      type: Object,
      default: () => {},
    },
  },
};
</script>

<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <v-card flat>
          <div class="headline">
            {{ item.name }}
          </div>
          <div class="subtitle-1">
            {{ item.omics_type }}
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
