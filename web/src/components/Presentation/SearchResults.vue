<script lang="ts">
import { defineComponent, PropType, ref } from '@vue/composition-api';

import { BaseSearchResult } from '@/data/api';

export default defineComponent({
  props: {
    page: {
      type: Number,
      required: true,
    },
    itemsPerPage: {
      type: Number,
      required: true,
    },
    count: {
      type: Number,
      required: true,
    },
    titleKey: {
      type: String,
      default: 'name',
    },
    subtitleKey: {
      type: String,
      default: 'description',
    },
    results: {
      type: Array as PropType<BaseSearchResult[]>,
      default: () => [],
    },
    icon: {
      type: String,
      default: 'mdi-book',
    },
    disableNavigateOnClick: {
      type: Boolean,
      default: false,
    },
    disablePagination: {
      type: Boolean,
      default: false,
    },
  },
  setup(props) {
    const rows = ref(props.itemsPerPage);
    return {
      rows,
    };
  },

});

</script>

<template>
  <div>
    <v-col
      v-if="!disablePagination"
      cols="12"
    >
      <v-row
        no-gutters
        justify="center"
      >
        <v-col
          cols="3"
        >
          <v-pagination

            :value="page"
            :length="Math.ceil(count / rows)"
            :total-visible="7"
            class="pt-3"
            depressed
            @input="$emit('set-page', $event)"
          />
        </v-col>
        <v-col cols="1">
          <v-select
            v-model="rows"
            :items="[5, 10, 15, 20]"
            label="Items per page"
            class="px-4"
            @input="$emit('set-items-per-page', $event)"
          />
        </v-col>
      </v-row>
    </v-col>
    <v-list dense>
      <template
        v-for="(result, resultIndex) in results"
      >
        <v-divider
          v-if="resultIndex > 0"
          :key="`${result.id}-divider`"
        />

        <v-list-item
          :key="result.id"
          :ripple="!disableNavigateOnClick"
          :inactive="disableNavigateOnClick"
          v-on="{
            click: disableNavigateOnClick
              ? () => {}
              : () => $emit('selected', result.id),
          }"
        >
          <slot
            name="action"
            v-bind="{ result }"
          />
          <v-list-item-avatar>
            <v-icon
              v-if="result.children && result.children.length > 0 && result.study_category === 'research_study'"
            >
              mdi-book-multiple-outline
            </v-icon>
            <v-icon
              v-else
            >
              {{ icon }}
            </v-icon>
          </v-list-item-avatar>
          <v-list-item-content>
            <v-list-item-title>
              {{ result[titleKey] }}
              <slot
                name="child-list"
                v-bind="{ result}"
              />
            </v-list-item-title>
            <v-list-item-subtitle>
              <slot
                name="subtitle"
                v-bind="{ result }"
              >
                {{ result[subtitleKey] || 'No description' }}
              </slot>
            </v-list-item-subtitle>
            <slot
              name="item-content"
              v-bind="{ result }"
            />
          </v-list-item-content>

          <slot
            name="action-right"
            v-bind="{ result }"
          />
        </v-list-item>
      </template>
    </v-list>
  </div>
</template>
