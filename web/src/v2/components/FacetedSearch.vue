<script lang="ts">
import Vue, { PropType } from 'vue';
import { groupBy } from 'lodash';
import { fieldDisplayName } from '@/util';
import * as encoding from '@/encoding';
import { Condition, entityType } from '@/data/api';

export interface SearchFacet {
  field: string;
  table: entityType;
  group?: string;
}

type KeyedFieldData = encoding.FieldsData & SearchFacet & { key: string; };

export default Vue.extend({
  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    fields: {
      type: Array as PropType<SearchFacet[]>,
      required: true,
    },
  },
  data() {
    return {
      fieldmeta: encoding.fields,
      filterText: '',
      menuState: {} as Record<string, boolean>,
    };
  },
  computed: {
    privatefilteredFields(): SearchFacet[] {
      if (this.filterText) {
        return this.fields.filter(({ field }) => {
          const lower = this.filterText.toLowerCase();
          return field.toLowerCase().indexOf(lower) >= 0;
        });
      }
      return this.fields;
    },
    groupedFields(): [string, KeyedFieldData[]][] {
      const fieldsWithMeta = this.privatefilteredFields
        .map((sf) => ({
          key: `${sf.table}_${sf.field}`,
          ...sf,
          ...encoding.fields[sf.field],
        }))
        .filter(({ hideFacet }) => !hideFacet)
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
        <template v-for="sf in filteredFields">
          <v-menu
            :key="sf.key"
            offset-x
            :close-on-content-click="false"
            @input="toggleMenu(sf.key, $event)"
          >
            <template #activator="{ on }">
              <v-list-item
                v-show="!hasActiveConditions(sf.key)"
                v-on="on"
              >
                <v-list-item-content>
                  <v-list-item-title> {{ fieldDisplayName(sf.key) }} </v-list-item-title>
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
                  field: sf.field,
                  table: sf.table,
                  isOpen: menuState[sf.key],
                }"
              />
            </v-card>
          </v-menu>
        </template>
      </div>
    </v-list>
  </div>
</template>
