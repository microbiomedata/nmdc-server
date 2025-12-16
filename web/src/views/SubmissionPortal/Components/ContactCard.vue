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

    const items = [
      {
        title: 'Visit our support page',
        icon: 'mdi-open-in-new',
        color: 'primary',
        link: 'https://microbiomedata.org/contact/',
      },
      {
        title: 'Send us a message',
        subtitle: 'Ask us for help',
        icon: 'mdi-email',
        color: 'blue',
        link: emailTemplate('support'),
      },
      {
        title: 'Report an issue',
        subtitle: 'Let us know of any bugs',
        icon: 'mdi-bug',
        color: 'red',
        link: emailTemplate('bug'),
      },
      {
        title: 'Request a feature',
        subtitle: 'Suggest a new feature',
        icon: 'mdi-plus-circle',
        color: 'grey-darken-2',
        link: emailTemplate('feature'),
      }
    ]

    return {
      items,
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
      <v-list>
        <v-list-item
          v-for="item in items"
          :key="item.title"
          :href="item.link"
          :title="item.title"
          :base-color="item.color"
          lines="two"
          class="mb-2 bg-grey-lighten-3"
        >
          <template #subtitle>
            <div class="text-grey-darken-4">
              {{ item.subtitle }}
            </div>
          </template>
          <template #prepend>
            <v-icon :style="{opacity: 1}">
              {{ item.icon }}
            </v-icon>
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>
