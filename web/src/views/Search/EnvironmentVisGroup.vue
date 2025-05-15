<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
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
      <div
        class="pr-2 overflow-y-auto overflow-x-hidden"
        style="
            height: 700px;
            width: 100%;
            max-width: 100%;
          "
      >
        <EcosystemSankey
          :conditions="conditions"
          style="width: 100%"
          @selected="toggleConditions($event.conditions)"
        />
      </div>
    </v-col>
  </v-row>
</template>
