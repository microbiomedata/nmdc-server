<script lang="ts">
import { computed, defineComponent } from 'vue';

export default defineComponent({
  props: {
    baseUrl: {
      type: String,
      default: 'https://nmdc-documentation.readthedocs.io/en/latest/howto_guides/submit2nmdc.html',
    },
    anchor: {
      type: String,
      default: '',
    },
  },
  setup(props) {
    const fullUrl = computed(() => props.baseUrl + (props.anchor ? `#${props.anchor}` : ''));
    return {
      fullUrl,
    };
  },
});
</script>

<template>
  <v-tooltip bottom>
    View documentation
    <template #activator="{ on, attrs }">
      <a
        class="ml-2"
        :href="fullUrl"
        target="_blank"
        rel="noopener noreferrer"
        v-bind="attrs"
        v-on="on"
      >
        <v-btn
          color="primary"
          text
          icon
        >
          <v-icon size="24px">
            mdi-information
          </v-icon>
        </v-btn>
      </a>
    </template>
  </v-tooltip>
</template>
