<script lang="ts">
import { defineComponent, ref } from 'vue';
import { SubmissionStatusEnum, status } from '../store';

export default defineComponent({
  components: {},
  setup() {
    const message = ref(`This submission has status "${SubmissionStatusEnum[status.value].title}" and cannot be edited.`);
    return {
      message,
      status,
    };
  },
});
</script>

<template>
  <v-alert
    :text="message"
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
