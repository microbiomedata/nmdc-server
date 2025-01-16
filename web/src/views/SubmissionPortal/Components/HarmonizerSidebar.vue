<script lang="ts">
import {
  defineComponent, ref,
} from '@vue/composition-api';

export default defineComponent({
  setup() {
    const tab = ref(0);

    return {
      tab,
    };
  },
});
</script>

<template>
  <div class="harmonizer-sidebar-content">
    <v-tabs
      v-model="tab"
      grow
    >
      <v-tab>
        <v-icon>mdi-information-outline</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-magnify</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-assistant</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-swap-vertical</v-icon>
      </v-tab>
      <v-tab>
        <v-icon>mdi-help-circle-outline</v-icon>
      </v-tab>
    </v-tabs>

    <v-tabs-items v-model="tab">
      <v-tab-item>
        COLUMN INFO
      </v-tab-item>
      <v-tab-item>
        FIND AND REPLACE
      </v-tab-item>
      <v-tab-item>
        SUGGESTER
      </v-tab-item>
      <v-tab-item>
        IMPORT / EXPORT
      </v-tab-item>
      <v-tab-item>
        SITE HELP
      </v-tab-item>
    </v-tabs-items>
  </div>
</template>

<style lang="scss" scoped>
.harmonizer-sidebar-content {
  .v-tab {
    min-width: 10px;
  }
}
</style>
