<script lang="ts">
import {
  defineComponent, PropType, toRef, watch,
} from '@vue/composition-api';
import AuthButton from '@/components/Presentation/AuthButton.vue';
import { stateRefs } from '@/store';
import useRequest from '@/use/useRequest';
import { loadRecord } from './store';

export default defineComponent({
  components: { AuthButton },
  props: {
    id: {
      type: String as PropType<string | null>,
      default: null,
    },
  },
  setup(props) {
    const req = useRequest();

    function load() {
      const { id } = props;
      if (id) req.request(() => loadRecord(id));
      else req.reset();
    }

    watch(toRef(props, 'id'), load);
    load();

    return { stateRefs, req };
  },
});
</script>

<template>
  <v-main>
    <v-container v-if="!stateRefs.user.value && !req.loading.value">
      <h1>NMDC Submission Portal</h1>
      <p>
        This system requires authentication.
        <a href="https://support.orcid.org/hc/en-us/articles/360006973953">ORCID registration is free for individuals.</a>
      </p>
      <AuthButton />
    </v-container>
    <router-view v-else-if="!req.loading.value && !req.error.value" />
    <div
      v-else-if="req.loading.value"
      class="text-h3"
    >
      Submission portal is loading...
    </div>
    <div
      v-else-if="req.error.value"
    >
      <v-container>
        <v-alert type="error">
          <div class="text-h6">
            Error loading record {{ id }}
          </div>
          {{ req.error.value }}
        </v-alert>
      </v-container>
    </div>
  </v-main>
</template>
