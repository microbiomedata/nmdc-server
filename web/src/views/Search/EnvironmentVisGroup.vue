<script setup lang="ts">
import EcosystemSankey from '@/components/EcosystemSankey.vue';
import HelpWrapper from '@/components/HelpWrapper.vue';
import { toggleConditions } from '@/store';
import { Condition } from '@/data/api';

defineProps<{
  conditions: Condition[];
}>();
</script>

<template>
  <v-row>
    <v-col :cols="12">
      <HelpWrapper
        height="360px"
        help-text="this is cool"
        allow-fullscreen
      >
        <EcosystemSankey
          :conditions="conditions"
          style="width: 100%; padding: 1rem"
          @selected="toggleConditions($event.conditions)"
        />
      </HelpWrapper>
    </v-col>
  </v-row>
</template>