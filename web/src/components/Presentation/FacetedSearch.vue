<template>
  <v-list
    ref="list"
    dense
    class="compact"
  >
    <template v-for="(values, field) in facetSummaries">
      <template
        v-if="!(fields[field] && (fields[field].hide || fields[field].hideFacet))
          && values.length && values[0].count > 1"
      >
        <v-subheader :key="field">
          {{ fieldDisplayName(field) }}
        </v-subheader>
        <v-list-item-group
          :key="`${field}-item`"
          multiple
        >
          <v-list-item
            v-for="val in values.slice(0, valueCount[field])"
            :key="val.facet"
            :disabled="val.count === 0"
            :value="val.facet"
            class="overflow"
          >
            <v-list-item-content>
              {{ valueDisplayName(field, val.facet) }}
            </v-list-item-content>
            <v-list-item-action>
              <v-list-item-action-text v-text="val.count" />
            </v-list-item-action>
          </v-list-item>
        </v-list-item-group>
        <v-list-item
          v-if="valueCount[field] < values.length"
          :key="`${field}-more`"
          @click="valueCount[field] += 10"
        >
          <v-list-item-content
            class="blue--text text--darken-4 caption"
          >
            more
          </v-list-item-content>
        </v-list-item>
        <v-list-item
          v-if="valueCount[field] > 5"
          :key="`${field}-less`"
          @click="valueCount[field] = 5"
        >
          <v-list-item-content
            class="blue--text text--darken-4 caption"
          >
            less
          </v-list-item-content>
        </v-list-item>
      </template>
    </template>
  </v-list>
</template>
<script>
import { fieldDisplayName, valueDisplayName } from '@/util';
import * as encoding from '@/encoding';

export default {
  props: {
    type: {
      type: String,
      default: 'study',
    },
    conditions: {
      type: Array,
      default: () => [],
    },
    facetSummaries: {
      type: Object,
      default: () => ({}),
    },
  },
  data: () => ({
    valueCount: {},
    fields: encoding.fields,
  }),
  methods: {
    fieldDisplayName,
    valueDisplayName,
  },
};
</script>
<style scoped>
.overflow {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.v-list--dense.compact .v-list-item {
  min-height: 10px;
}
.v-list--dense.compact .v-list-item .v-list-item__content {
  padding: 0;
}
.v-list--dense.compact .v-list-item .v-list-item__action {
  margin: 0 0 0 16px;
}
</style>
