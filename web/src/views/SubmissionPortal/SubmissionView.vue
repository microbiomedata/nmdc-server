<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import AuthButton from '@/components/Presentation/AuthButton.vue';
import { stateRefs } from '@/store';

export default defineComponent({
  components: { AuthButton },
  setup() { return { stateRefs }; },
});
</script>

<template>
  <v-main>
    <v-container v-if="!stateRefs.user.value">
      <h1>Metadata Submission Portal</h1>
      <p>This system requires ORCiD Authentication.</p>
      <AuthButton />
    </v-container>
    <keep-alive v-else>
      <router-view />
    </keep-alive>
  </v-main>
</template>
