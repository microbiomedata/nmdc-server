<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  toRef,
  watch,
} from '@vue/composition-api';
import { stateRefs } from '@/store';
import useRequest from '@/use/useRequest';
import { loadRecord } from './store';
import AppBanner from '@/components/AppBanner.vue';
import TitleBanner from '@/views/SubmissionPortal/Components/TitleBanner.vue';
import IntroBlurb from '@/views/SubmissionPortal/Components/IntroBlurb.vue';
import IconBar from '@/views/SubmissionPortal/Components/IconBar.vue';
import LoginPrompt from '@/views/SubmissionPortal/Components/LoginPrompt.vue';

export default defineComponent({
  components: {
    AppBanner,
    IconBar,
    IntroBlurb,
    LoginPrompt,
    TitleBanner,
  },
  props: {
    id: {
      type: String as PropType<string | null>,
      default: null,
    },
  },
  setup(props, { root }) {
    const req = useRequest();

    function load() {
      const { id } = props;
      if (id) req.request(() => loadRecord(id));
      else req.reset();
    }

    watch(toRef(props, 'id'), load);
    load();

    const showBanner = computed(() => root.$route.path === '/submission/home');

    return { stateRefs, req, showBanner };
  },
});
</script>

<template>
  <v-main>
    <v-container v-if="!stateRefs.user.value && !req.loading.value">
      <v-container class="mt-4">
        <v-row>
          <v-col class="pb-0">
            <TitleBanner />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <LoginPrompt />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <IconBar />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <IntroBlurb />
          </v-col>
        </v-row>
      </v-container>
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
