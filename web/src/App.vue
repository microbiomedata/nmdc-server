<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import AppHeader from '@/components/Presentation/AppHeader.vue';
import { stateRefs } from '@/store/';

export default defineComponent({
  name: 'App',
  components: { AppHeader },
  setup() {
    return {
      stateRefs,
    };
  },
});
</script>

<template>
  <v-app>
    <app-header />
    <keep-alive>
      <router-view />
    </keep-alive>
  </v-app>
</template>
