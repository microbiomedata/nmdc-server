<script lang="ts">
import Vue, { PropType } from 'vue';
import { groupBy } from 'lodash';
import { fieldDisplayName } from '@/util';
import * as encoding from '@/encoding';
import { Condition } from '@/data/api';

type KeyedFieldData = encoding.FieldsData & { key: string; };

export default Vue.extend({
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
  data() {
    return {
      filterText: '',
      menuState: {} as Record<string, boolean>,
    };
  },
  computed: {
    privatefilteredFields(): string[] {
      if (this.filterText) {
        return this.fields.filter((f) => {
          const lower = this.filterText.toLowerCase();
          return f.toLowerCase().indexOf(lower) >= 0;
        });
      }
      return this.fields;
    },
    groupedFields(): [string, KeyedFieldData[]][] {
      const fieldsWithMeta = this.privatefilteredFields
        .map((f) => ({ key: f, ...encoding.getField(f) }))
        .filter((f) => !f.hideFacet)
        .sort(((a, b) => (a.sortKey || 0) - (b.sortKey || 0)));
      return Object.entries(groupBy(fieldsWithMeta, 'group'))
        .sort((a) => ((a[0] === 'undefined') ? 0 : -1));
    },
  },
  methods: {
    fieldDisplayName,
    toggleMenu(category: string, value: boolean): void {
      Vue.set(this.menuState, category, value);
    },
    hasActiveConditions(category: string): boolean {
      return this.conditions.some((cond) => cond.field === category);
    },
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
      outlined
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
        <template v-for="field in filteredFields">
          <v-menu
            :key="field.key"
            offset-x
            :close-on-content-click="false"
            @input="toggleMenu(field.key, $event)"
          >
            <template #activator="{ on }">
              <v-list-item
                v-show="!hasActiveConditions(field.key)"
                v-on="on"
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
                  type: field.type,
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
