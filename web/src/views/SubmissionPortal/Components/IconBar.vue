<script lang="ts">
import {
  defineComponent,
} from 'vue';

export default defineComponent({});
</script>

<template>
  <v-container class="mt-4 limited-width">
    <v-row>
      <v-col>
        <a
          target="_blank"
          title="View the how-to guide"
          href="https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html"
          rel="noreferrer noopener"
          class="text-decoration-none"
        >
          <v-container>
            <v-row class="align-center flex-nowrap">
              <v-col cols="4">
                <v-avatar color="primary">
                  <v-icon color="white">
                    mdi-timer-outline
                  </v-icon>
                </v-avatar>
              </v-col>
              <v-col>
                <span class="text-blue text-left text-h6 font-weight-bold">
                  Quickstart
                </span>
              </v-col>
            </v-row>
          </v-container>
        </a>
      </v-col>
      <v-col>
        <a
          target="_blank"
          title="View the submission portal tutorial"
          href="https://nmdc-documentation.readthedocs.io/en/latest/tutorials/submission_portal.html"
          rel="noreferrer noopener"
          class="text-decoration-none"
        >
          <v-container>
            <v-row class="align-center flex-nowrap">
              <v-col cols="4">
                <v-avatar color="primary">
                  <v-icon color="white">
                    mdi-human-male-board
                  </v-icon>
                </v-avatar>
              </v-col>
              <v-col>
                <span class="text-blue text-left text-h6 font-weight-bold">
                  Tutorial
                </span>
              </v-col>
            </v-row>
          </v-container>
        </a>
      </v-col>
      <v-col>
        <a
          target="_blank"
          title="View the metadata schema"
          href="https://w3id.org/nmdc/about"
          rel="noreferrer noopener"
          class="text-decoration-none"
        >
          <v-container>
            <v-row class="align-center flex-nowrap">
              <v-col cols="4">
                <v-avatar color="primary">
                  <v-icon color="white">
                    mdi-book-open-variant-outline
                  </v-icon>
                </v-avatar>
              </v-col>
              <v-col>
                <span class="text-blue text-left text-h6 font-weight-bold">
                  Reference
                </span>
              </v-col>
            </v-row>
          </v-container>
        </a>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.limited-width {
  max-width: 800px;
}
</style>
