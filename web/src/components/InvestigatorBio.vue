<script lang="ts">
import { StudySearchResults } from '@/data/api';
import { defineComponent, PropType } from '@vue/composition-api';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<StudySearchResults>,
      required: true,
    },
  },
});
</script>

<template>
  <v-row class="mx-2">
    <v-col
      class="shrink"
      offset="1"
    >
      <v-avatar :size="200">
        <v-img :src="item.principal_investigator_image_url" />
      </v-avatar>
    </v-col>
    <v-col class="grow">
      <v-row
        align="center"
        justify="start"
        style="height: 100%"
      >
        <v-card flat>
          <div class="headline">
            {{ item.principal_investigator_name }}
          </div>
          <div class="caption">
            Principal investigator
          </div>
          <div
            v-for="site in item.principal_investigator_websites"
            :key="site"
            class="caption primary--text"
            style="cursor: pointer"
            @click="openLink(site)"
          >
            <v-icon
              small
              left
              color="primary"
            >
              mdi-link
            </v-icon>
            {{ site }}
          </div>
        </v-card>
      </v-row>
    </v-col>
  </v-row>
</template>
