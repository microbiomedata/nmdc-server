<script lang="ts">
import { defineComponent } from 'vue';
import { statusDisplay } from '../store';

export default defineComponent({
  setup() {
    return {
      statusDisplay,
    };
  },
});
</script>

<template>
  <v-alert
    :text="`This submission has status '${statusDisplay}' and cannot be edited.`"
    tile
    type="info"
    class="overflow-visible"
  >
    <template #append>
      <v-menu
        bottom
        offset-y
        :close-on-content-click="false"
        max-width="300"
      >
        <template #activator="{ props }">
          <v-icon
            v-bind="props"
            style="cursor: pointer;"
          >
            mdi-information
          </v-icon>
        </template>
        <v-card>
          <v-card-text>
            If you need to edit this submission, please contact:
            <span style="user-select: all; cursor: text; font-weight: bold;">support@microbiomedata.org</span>
          </v-card-text>
        </v-card>
      </v-menu>
    </template>
  </v-alert>
</template>
