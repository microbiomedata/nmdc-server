<script setup lang="ts">
import EcosystemSankey from '@/components/EcosystemSankey.vue';
import HelpWrapper from '@/components/HelpWrapper.vue';
import { toggleConditions } from '@/store';
import { Condition } from '@/data/api';
import { VISUALIZATION_HEIGHT } from '@/views/Search/types';

const helpSankey = 'This Sankey diagram shows samples by the hierarchical relationships between ecosystems, ecosystem categories, ecosystem types, ecosystem subtypes, and specific ecosystems. Click on a section to filter by that ecosystem.';

defineProps<{
  conditions: Condition[];
}>(); 
</script>

<template>
  <v-row>
    <v-col :cols="12">
      <HelpWrapper
        :height="VISUALIZATION_HEIGHT"
        :help-text="helpSankey"
        allow-fullscreen
      >
        <EcosystemSankey
          :conditions="conditions"
          :style="{
            width: '100%',
            padding: '1rem',
          }"
          @selected="toggleConditions($event.conditions)"
        />
      </HelpWrapper>
    </v-col>
  </v-row>
</template>