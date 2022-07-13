<script lang="ts">
import { computed, defineComponent, PropType } from '@vue/composition-api';
import { isObject } from 'lodash';

import { BaseSearchResult, BiosampleSearchResult } from '@/data/api';
import { getField } from '@/encoding';
import AttributeItem from './AttributeItem.vue';

export default defineComponent({
  components: { AttributeItem },

  props: {
    type: {
      type: String,
      default: '',
    },
    item: {
      type: Object as PropType<BaseSearchResult | BiosampleSearchResult>,
      required: true,
    },
  },

  setup(props) {
    const displayFields = computed(() => {
      const ret = Object.keys(props.item).filter((field) => {
        const value = props.item[field];
        if (['name', 'description'].includes(field)) {
          return false;
        }
        return !isObject(value) && value && (!getField(field) || !getField(field).hideAttr);
      });

      // add geo_loc_name to after lat/lon
      if (props.item?.annotations?.geo_loc_name !== undefined) {
        const geoLocIndex = ret.includes('latitude') ? ret.indexOf('latitude') + 1 : ret.length;
        ret.splice(geoLocIndex, 0, 'geo_loc_name');
      }

      return ret;
    });

    const alternateIdentifiers = computed(() => props.item.alternate_identifiers
      .map((id) => ({ name: id, target: `https://identifiers.org/${id}` })));

    return {
      // computed
      alternateIdentifiers,
      displayFields,
    };
  },
});
</script>

<template>
  <div>
    <div class="display-1">
      Attributes
    </div>
    <v-list
      style="column-count: 3;"
      class="d-block py-4"
    >
      <v-col
        v-for="field in displayFields"
        :key="field"
        class="pa-0 d-inline-block"
      >
        <AttributeItem v-bind="{ item, field }" />
      </v-col>
    </v-list>
    <v-list v-if="alternateIdentifiers.length > 0">
      <div class="display-1">
        Alternative Identifiers
      </div>
      <AttributeItem
        v-for="({ name, target }) in alternateIdentifiers"
        :key="name"
        v-bind="{ item, field, link: { name, target } }"
      />
    </v-list>
  </div>
</template>
