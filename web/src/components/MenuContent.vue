<script lang="ts">
import {
  defineComponent, PropType, onBeforeUnmount, computed,
} from '@vue/composition-api';
// @ts-ignore
import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';

import { fieldDisplayName } from '@/util';
import { getField, geneFunctionTypeInfo, geneFunctionTables } from '@/encoding';
import FacetSummaryWrapper from '@/components/Wrappers/FacetSummaryWrapper.vue';
import FilterDate from '@/components/Presentation/FilterDate.vue';
import FilterFloat from '@/components/Presentation/FilterFloat.vue';
import FilterList from '@/components/Presentation/FilterList.vue';
import FilterSankeyTree from '@/components/FilterSankeyTree.vue';
import FilterGene from '@/components/FilterGene.vue';
import FilterTree from '@/components/FilterTree.vue';
import { urlify } from '@/data/utils';
import { AttributeSummary, Condition, entityType } from '@/data/api';

export default defineComponent({
  components: {
    FacetSummaryWrapper,
    FilterDate,
    FilterFloat,
    FilterList,
    FilterGene,
    FilterSankeyTree,
    FilterTree,
  },

  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String as PropType<entityType>,
      required: true,
    },
    summary: {
      type: Object as PropType<AttributeSummary>,
      required: true,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    update: {
      type: Boolean,
      default: false,
    },
  },

  setup(props, { emit }) {
    onBeforeUnmount(() => emit('close'));

    const description = computed(() => {
      const fieldSchemaName = getField(props.field, props.table);
      const schemaName = fieldSchemaName.schemaName || props.field;
      if (schemaName !== undefined) {
        const schema = NmdcSchema.classes[schemaName] || NmdcSchema.slots[schemaName];
        // Avoid restating the field name as a description
        if (schema && schema.description !== schemaName) {
          return schema?.description || '';
        }
      }
      return '';
    });

    return {
      description,
      fieldDisplayName,
      getField,
      urlify,
      geneFunctionTypeInfo,
      geneFunctionTables,
    };
  },
});
</script>

<template>
  <div>
    <v-card-title class="pb-0">
      {{ fieldDisplayName(field, table) }}
      <span
        v-if="summary.units"
        class="pl-2"
      >
        ({{ summary.units.name }})
      </span>
      <v-spacer />
      <v-btn
        icon
        @click="$emit('close')"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text
      v-if="description"
      class="py-1 text-caption"
      v-html="urlify(description)"
    />
    <template v-if="isOpen">
      <filter-list
        v-if="summary.type === 'string'"
        :field="field"
        :table="table"
        :conditions="conditions"
        @select="$emit('select', $event)"
      />
      <FilterGene
        v-if="geneFunctionTables.includes(summary.type)"
        :field="field"
        :table="table"
        :conditions="conditions"
        :gene-type-params="geneFunctionTypeInfo[summary.type.split('_')[0]]"
        :gene-type="summary.type.split('_')[0]"
        @select="$emit('select', $event)"
      />
      <filter-date
        v-if="summary.type === 'date'"
        v-bind="{
          field, type: table, conditions,
          min: summary.min,
          max: summary.max,
          update,
        }"
        class="pa-5"
        @select="$emit('select', $event)"
      />
      <filter-float
        v-else-if="['float', 'integer'].includes(summary.type)"
        v-bind="{
          field, type: table, conditions,
          min: summary.min,
          max: summary.max,
          update,
        }"
        class="pa-5"
        @select="$emit('select', $event)"
      />
      <filter-sankey-tree
        v-else-if="['sankey-tree'].includes(summary.type)"
        v-bind="{ field, table, conditions }"
        @select="$emit('select', $event)"
      />
      <facet-summary-wrapper
        v-else-if="['tree'].includes(summary.type)"
        v-bind="{ table, field, conditions }"
      >
        <template #default="props">
          <filter-tree
            v-bind="props"
            @select="$emit('select', $event)"
          />
        </template>
      </facet-summary-wrapper>
    </template>
  </div>
</template>
