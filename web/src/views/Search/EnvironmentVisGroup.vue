<script lang="ts">
import { defineComponent, PropType } from 'vue';
import EcosystemSankey from '@/components/EcosystemSankey.vue';

import {
  toggleConditions,
} from '@/store';
import { Condition } from '@/data/api';

export default defineComponent({
  components: {
    EcosystemSankey,
  },

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },

  setup() {
    return {
      toggleConditions,
    };
  },
});
</script>

<template>
  <v-row>
    <v-col :cols="12">
      <EcosystemSankey
        :conditions="conditions"
        style="width: 100%"
        @selected="toggleConditions($event.conditions)"
      />
    </v-col>
  </v-row>
</template>
