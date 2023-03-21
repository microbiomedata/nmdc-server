<script lang="ts">
import { defineComponent } from '@vue/composition-api';
import AuthButton from '@/components/Presentation/AuthButton.vue';
import Menus from '@/menus';

export default defineComponent({
  components: {
    AuthButton,
  },
  setup() {
    return {
      Menus,
    };
  },
});
</script>

<template>
  <v-app-bar
    app
    class="navigation-button-text-animate"
    color="white"
    clipped-left
    elevation="4"
    height="82"
  >
    <a
      class="header-logo"
      href="https://microbiomedata.org/"
    >
      <img
        src="/NMDC_logo_long.jpg"
        alt="Home page"
      >
    </a>

    <v-spacer />

    <template v-for="(menu) in Menus">
      <v-btn
        v-if="!menu.items || !menu.items.length"
        :key="menu.label"
        plain
        small
        :ripple="false"
        :href="menu.href"
      >
        <div class="navigation-button-text">
          {{ menu.label }}
        </div>
      </v-btn>

      <v-menu
        v-else
        :key="menu.label"
        bottom
        right
        offset-y
        content-class="navigation-button-text-animate elevation-4"
        :open-on-hover="true"
        transition="fade-transition"
      >
        <template #activator="{ on, attrs }">
          <v-btn
            plain
            small
            :ripple="false"
            :href="menu.href"
            v-bind="attrs"
            v-on="on"
          >
            <div class="navigation-button-text">
              {{ menu.label }}
            </div>
            <v-icon small>
              mdi-chevron-down
            </v-icon>
          </v-btn>
        </template>

        <v-list
          dense
          expand
          flat
          nav
        >
          <v-list-item
            v-for="item in menu.items"
            :key="item.label"
            :href="item.href"
            :to="item.to"
            :ripple="false"
            class="text-uppercase"
          >
            <v-list-item-content>
              <v-list-item-title>
                <div class="navigation-button-text">
                  {{ item.label }}
                </div>
              </v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>

    <v-divider vertical />

    <AuthButton nav />
  </v-app-bar>
</template>

<style lang="scss" scoped>
  .header-logo {
    height: 100%;
    img {
      padding: 9px 0;
      height: 100%;
    }
  }

  .navigation-button-text-animate {
    .navigation-button-text {
      display: inline-block;
      padding: 2px 0;
      background-image: linear-gradient(var(--v-primary-base), var(--v-primary-base));
      background-position: 0 100%;
      background-repeat: no-repeat;
      background-size: 0 1px;
      transition-property: background-size;
      transition-duration: 0.15s;
      transition-timing-function: ease;
    }

    .v-btn, .v-list-item {
      &.v-btn--active, &:hover, &:focus, &.v-list-item--active {
        .navigation-button-text {
          color: var(--v-primary-base);
          background-size: 100% 1px;
        }
      }
    }
  }
</style>
