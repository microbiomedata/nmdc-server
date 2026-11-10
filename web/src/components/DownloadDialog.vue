<script lang="ts" setup>
const {
  href = undefined,
  loading = false,
  isStreaming = false,
} = defineProps<{
  href?: string;
  loading?: boolean;
  isStreaming?: boolean;
}>();

defineEmits<{
  clicked: [];
}>();
</script>

<template>
  <v-card>
    <v-card-text>
      <div v-if="isStreaming" class="mb-3">
        <h2 class="mb-2">
          Streaming Data
        </h2>
        <div class="mb-3">
          The data you are about to download will be streamed to a zip file in your Downloads folder. Once your browser indicates that the download is in progress, you may leave or close this tab but <strong>you cannot quit your browser completely until the download is complete</strong>.
        </div>
        <div>
          Large downloads can take hours to complete. Please ensure that you have a stable internet connection and sufficient bandwidth to download the data.
        </div>
      </div>
      <div>
        <h2 class="mb-2">
          Terms and Conditions
        </h2>
        <div class="mb-3">
          These data are made available under the
          <a href="https://creativecommons.org/licenses/by/4.0/">
            Creative Commons Attribution 4.0 International license</a>.
          The data may be used provided the original data
          contributor is cited.
        </div>
        <div>
          For more information on the NMDC Data Policy see
          <a href="https://microbiomedata.org/nmdc-data-use-policy/">
            https://microbiomedata.org/nmdc-data-use-policy/
          </a>
        </div>
      </div>
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        text
        :href="href"
        :loading="loading"
        target="_blank"
        rel="noopener"
        @click="$emit('clicked')"
      >
        Accept and continue to download
      </v-btn>
    </v-card-actions>
  </v-card>
</template>
