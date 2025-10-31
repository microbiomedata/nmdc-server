<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { groupBy } from 'lodash';

// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import * as encoding from '@/encoding';
import { Condition, entityType } from '@/data/api';

const groupOrders = [
  'study',
  'function',
  'sample',
  'gold ecosystems',
  'mixs environmental triad',
  'data generation',
  'workflow execution',
];

export interface SearchFacet {
  field: string;
  table: entityType;
  group?: string;
}

type KeyedFieldData = encoding.FieldsData & SearchFacet & { key: string; };

export default defineComponent({
  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    fields: {
      type: Array as PropType<SearchFacet[]>,
      required: true,
    },
    filterText: {
      type: String,
      required: true,
    },
    facetValues: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },
  data() {
    return {
      menuState: {} as Record<string, boolean>,
    };
  },
  computed: {
    privatefilteredFields(): SearchFacet[] {
      const { filterText } = this;
      if (filterText) {
        return this.fields.filter(({ field, table }) => {
          const lower = filterText.toLowerCase();
          return (
            field.toLowerCase().indexOf(lower) >= 0
            || fieldDisplayName(field, table).toLowerCase().indexOf(lower) >= 0
          );
        });
      }
      return this.fields;
    },
    groupedFields(): [string, KeyedFieldData[]][] {
      const fieldsWithMeta = this.privatefilteredFields
        .map((sf) => ({
          key: `${sf.table}_${sf.field}`,
          ...sf,
          ...encoding.getField(sf.field, sf.table),
        }))
        .filter(({ hideFacet }) => !hideFacet)
        .sort(((a, b) => (a.sortKey || 0) - (b.sortKey || 0)));
      return Object.entries(groupBy(fieldsWithMeta, 'group'))
        .sort(([a], [b]) => {
          const ai = groupOrders.indexOf(a.toLowerCase());
          const bi = groupOrders.indexOf(b.toLowerCase());
          return ai - bi;
        });
    },
    goldDescription() {
      // @ts-ignore
      const schema = NmdcSchema.slots.gold_path_field;
      return schema.annotations?.tooltip?.value || '';
    },
    mixsDescription() {
      // @ts-ignore
      const schema = NmdcSchema.slots.mixs_env_triad_field;
      return schema.annotations?.tooltip?.value || '';
    },
  },
  methods: {
    fieldDisplayName,
    toggleMenu(category: string, value: boolean): void {
      this.menuState[category] = value;
    },
    hasActiveConditions(category: string): boolean {
      return this.conditions.some((cond) => `${cond.table}_${cond.field}` === category);
    },
    tableName(table: string): string {
      if (table === 'study') {
        return 'Study';
      }
      if (table === 'biosample') {
        return 'Biosample';
      }
      if (table === 'omics_processing') {
        return 'Omics Processing';
      }
      return '';
    },
  },
});
</script>

<template>
  <div>
    <v-text-field
      :model-value="filterText"
      label="search"
      clearable
      class="mx-3 pt-1"
      hide-details
      variant="outlined"
      density="compact"
      append-inner-icon="mdi-magnify"
      @update:model-value="$emit('update:filterText', $event || '')"
    />
    <v-list
      ref="list"
      density="compact"
      shaped
      class="compact"
    >
      <div
        v-for="[groupname, filteredFields] in groupedFields"
        :key="groupname"
      >
        <v-list-subheader
          v-show="groupedFields.length > 1 && filteredFields.length > 0"
        >
          {{ groupname !== 'undefined' ? groupname : 'Other' }}
          <v-tooltip
            v-if="groupname === 'GOLD Ecosystems'"
            location="end"
            open-delay="600"
          >
            <template #activator="{ props }">
              <v-btn
                icon
                variant="plain"
                size="x-small"
                v-bind="props"
                class="ml-2"
              >
                <v-icon>mdi-help-circle</v-icon>
              </v-btn>
            </template>
            <span> {{ goldDescription }}</span>
          </v-tooltip>
          <v-tooltip
            v-if="groupname === 'MIxS Environmental Triad'"
            location="end"
            open-delay="600"
          >
            <template #activator="{ props }">
              <v-btn
                icon
                variant="plain"
                size="x-small"
                v-bind="props"
                class="ml-2"
              >
                <v-icon>mdi-help-circle</v-icon>
              </v-btn>
            </template>
            <span> {{ mixsDescription }}</span>
          </v-tooltip>
        </v-list-subheader>
        <template v-for="sf in filteredFields" :key="sf.key">
          <v-menu
            :model-value="menuState[sf.key]"
            location="end"
            :close-on-content-click="false"
            @update:model-value="toggleMenu(sf.key, $event)"
          >
            <template #activator="{ props }">
              <v-list-item
                v-show="!hasActiveConditions(sf.key)"
                v-bind="props"
              >
                <v-list-item-title>
                  {{ fieldDisplayName(sf.field, sf.table) }}
                </v-list-item-title>
                <template #append>
                  <v-icon>mdi-play</v-icon>
                </template>
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
                  toggleMenu: (val: boolean) => toggleMenu(sf.key, val),
                }"
              />
            </v-card>
          </v-menu>
        </template>
      </div>
      <v-divider
        v-if="facetValues.length && groupedFields.length"
        class="my-2"
      />
      <v-list-subheader v-if="facetValues.length">
        Query Options
      </v-list-subheader>
      <v-list-item
        v-for="condition in facetValues"
        :key="`${condition.table}:${condition.field}:${condition.value}`"
        @click="$emit('select', condition)"
      >
        <v-list-item-title>
          {{ condition.value }}
        </v-list-item-title>
        <v-list-item-subtitle>
          {{ fieldDisplayName(condition.field) }}
          <span v-if="condition.op === 'like'">({{ tableName(condition.table) }})</span>
        </v-list-item-subtitle>
        <template #append>
          <v-icon>mdi-filter-plus</v-icon>
        </template>
      </v-list-item>
      <v-list-item
        v-if="facetValues.length === 0 && groupedFields.length === 0"
      >
        No search results
      </v-list-item>
    </v-list>
  </div>
</template>

<style scoped>
.compact .v-list-item-title {
  font-size: .8125rem;
  font-weight: 500;
  line-height: 1rem;
}

.compact .v-list-subheader {
  font-size: .75rem;
  height: 40px;
  padding-inline-start: 0.5rem !important;
}
</style>