<script lang="ts">
import { defineComponent } from '@vue/composition-api';

export default defineComponent({
  props: {
    width: {
      type: Number,
      default: 16,
    },
    name: {
      type: String,
      default: '',
    },
    orcidId: {
      type: String,
      required: true,
    },
    authenticated: {
      type: Boolean,
      required: true,
    },
  },
});
</script>

<template>
  <div :style="{display: 'flex'}">
    <a
      :href="`https://orcid.org/${orcidId}`"
      :style="{display: 'flex'}"
    >
      <span
        v-if="name"
        class="mr-1"
      >
        {{ name }}
      </span>
      <img
        :width="`${width}px`"
        alt="ORCID logo"
        src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
      >
      <span
        v-if="!name"
        class="ml-1"
      >
        {{ orcidId }}
      </span>
    </a>
    <!--span
      v-if="!authenticated"
      class="ml-1"
    >
      (Unauthenticated)
    </span-->
  </div>
</template>
