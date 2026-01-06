<script lang="ts" setup>
const showDialog = defineModel<boolean>('show', { required: true });
</script>

<template>
  <v-dialog
    v-model="showDialog"
    :width="500"
  >
    <v-card>
      <v-card-title>
        <v-icon
          color="error"
        >
          mdi-alert-circle
        </v-icon>
        Download Failed
      </v-card-title>
      <v-card-text>
        Your download could not be completed at this time.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn
          color="primary"
          text
          @click="showDialog = false"
        >
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>