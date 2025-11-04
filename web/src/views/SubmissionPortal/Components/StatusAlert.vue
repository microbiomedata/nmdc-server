<script lang="ts">
import { defineComponent } from 'vue';
import {
  SubmissionStatusTitleMapping,
  status,
} from '../store';

export default defineComponent({
  components: {},
  setup() {
    return {
      status,
      SubmissionStatusTitleMapping,
    };
  },
});
</script>

<template>
  <v-alert
    type="info"
    class="ma-2"
  >
    <template #prepend>
      <v-menu
        bottom
        offset-y
        :close-on-content-click="false"
        max-width="300"
      >
        <template #activator="{ on, attrs }">
          <v-icon
            v-bind="attrs"
            style="cursor: pointer;"
            v-on="on"
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
    This submission has status "{{ SubmissionStatusTitleMapping[status] }}" and cannot be edited.
  </v-alert>
</template>
