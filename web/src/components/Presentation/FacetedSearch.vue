<script lang="ts">
import {
  defineComponent,
  computed,
  PropType,
  ref,
} from 'vue';
import { groupBy } from 'lodash';
import { fieldDisplayName } from '@/util';
import * as encoding from '@/encoding';
import { Condition } from '@/data/api';

export default defineComponent({
  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    fields: {
      type: Array as PropType<string[]>,
      required: true,
    },
  },

  setup(props) {
    const filterText = ref('');
    const menuState = ref({} as Record<string, boolean>);

    const privatefilteredFields = computed(() => {
      if (filterText.value) {
        return props.fields.filter((f) => {
          const lower = filterText.value.toLowerCase();
          return f.toLowerCase().indexOf(lower) >= 0;
        });
      }
      return props.fields;
    });

    const groupedFields = computed(() => {
      const fieldsWithMeta = privatefilteredFields.value
        .map((f) => ({ key: f, ...encoding.getField(f) }))
        .filter((f) => !f.hideFacet)
        .sort(((a, b) => (a.sortKey || 0) - (b.sortKey || 0)));
      return Object.entries(groupBy(fieldsWithMeta, 'group'))
        .sort((a) => ((a[0] === 'undefined') ? 0 : -1));
    });

    function toggleMenu(category: string, value: boolean): void {
      menuState.value[category] = value;
    }

    function hasActiveConditions(category: string): boolean {
      return props.conditions.some((cond) => cond.field === category);
    }

    return {
      filterText,
      menuState,
      privatefilteredFields,
      groupedFields,
      toggleMenu,
      hasActiveConditions,
      fieldDisplayName,
    };
  },
});
</script>

<template>
  <div>
    <v-text-field
      v-model="filterText"
      solo
      label="search"
      clearable
      class="mx-3"
      dense
      hide-details
      variant="outlined"
      flat
      append-icon="mdi-magnify"
    />
    <v-list
      ref="list"
      dense
      shaped
      class="compact"
    >
      <div
        v-for="[groupname, filteredFields] in groupedFields"
        :key="groupname"
      >
        <v-subheader
          v-show="groupedFields.length > 1 && filteredFields.length > 0"
        >
          {{ groupname !== 'undefined' ? groupname : 'Other' }}
        </v-subheader>
        <template v-for="field in filteredFields" :key="field.key">
          <v-menu
            location="end"
            :close-on-content-click="false"
            @update:model-value="toggleMenu(field.key, $event)"
          >
            <template #activator="{ props }">
              <v-list-item
                v-show="!hasActiveConditions(field.key)"
                v-bind="props"
              >
                <v-list-item-content>
                  <v-list-item-title> {{ fieldDisplayName(field.key) }} </v-list-item-title>
                </v-list-item-content>
                <v-list-item-icon>
                  <v-icon> mdi-play </v-icon>
                </v-list-item-icon>
              </v-list-item>
            </template>
            <v-card
              width="500"
            >
              <slot
                name="menu"
                v-bind="{
                  field: field.key,
                  isOpen: menuState[field.key],
                }"
              />
            </v-card>
          </v-menu>
        </template>
      </div>
    </v-list>
  </div>
</template>
