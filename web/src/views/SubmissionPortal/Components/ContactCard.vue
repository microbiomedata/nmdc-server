<script lang="ts">
import { defineComponent } from 'vue';

type EmailSubjects = 'support' | 'bug' | 'feature';

export default defineComponent({
  props: {
    elevation: {
      type: String,
      default: '24',
    },
  },
  setup() {
    function emailTemplate(value: EmailSubjects) {
      const subjects: { [_key in EmailSubjects]: string } = {
        support: 'Support Request',
        bug: 'Bug Report',
        feature: 'Feature Request',
      };
      const subject = encodeURIComponent(subjects[value]);
      return `mailto:support@microbiomedata.org?subject=${subject}`;
    }
    return {
      emailTemplate,
    };
  },
});
</script>
<template>
  <v-card
    :elevation="elevation"
  >
    <v-card-title>
      We are here to help
    </v-card-title>
    <v-card-text>
      <v-list
        subheader
      >
        <v-list-item
          two-line
          style="background-color: #eeeeee;"
          class="mb-2"
          href="https://microbiomedata.org/contact/"
        >
          <v-btn
            icon
            variant="outlined"
            color="primary"
            class="mr-4"
            style="border: solid #4F3B80;"
          >
            <v-icon
              color="primary"
            >
              mdi-open-in-new
            </v-icon>
          </v-btn>
          <v-list-item-title
            class="primary--text"
          >
            Visit our support page
          </v-list-item-title>
        </v-list-item>
        <v-list-item
          two-line
          class="mb-2"
          style="background-color: #eeeeee"
          :href="emailTemplate('support')"
        >
          <v-btn
            icon
            variant="outlined"
            color="blue"
            class="mr-4"
            style="border: solid;"
          >
            <v-icon>mdi-email</v-icon>
          </v-btn>
          <v-list-item-title
            class="blue--text"
          >
            Send us a message
          </v-list-item-title>
          <v-list-item-subtitle>
            Ask us for help
          </v-list-item-subtitle>
        </v-list-item>
        <v-list-item
          two-line
          class="mb-2"
          style="background-color: #eeeeee"
          :href="emailTemplate('bug')"
        >
          <v-btn
            icon
            variant="outlined"
            color="red"
            class="mr-4"
            style="border: solid;"
          >
            <v-icon>mdi-bug</v-icon>
          </v-btn>
          <v-list-item-title
            class="red--text"
          >
            Report an issue
          </v-list-item-title>
          <v-list-item-subtitle>
            Let us know of any bugs
          </v-list-item-subtitle>
        </v-list-item>
        <v-list-item
          two-line
          class="mb-2"
          style="background-color: #eeeeee"
          :href="emailTemplate('feature')"
        >
          <v-btn
            icon
            variant="outlined"
            color="grey darken-2"
            class="mr-4"
            style="border: solid;"
          >
            <v-icon>mdi-plus-circle</v-icon>
          </v-btn>
          <v-list-item-title
            class="grey--text text--darken-2"
          >
            Request a feature
          </v-list-item-title>
          <v-list-item-subtitle>
            Suggest a new feature
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>
