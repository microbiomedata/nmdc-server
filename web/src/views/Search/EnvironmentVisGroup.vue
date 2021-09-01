<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
import EcosystemSankey from '@/components/EcosystemSankey.vue';

import {
  toggleConditions,
} from '@/store';
import { Condition } from '@/data/api';

export default defineComponent({
  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },
  components: {
    EcosystemSankey,
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
