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
      const skipFields = new Set([
        'name',
        'description',
        'env_broad_scale_id',
        'env_local_scale_id',
        'env_medium_id',
      ]);
      const includeFields = new Set([
        'env_broad_scale',
        'env_local_scale',
        'env_medium',
      ]);
      const ret = Object.keys(props.item).filter((field) => {
        if (skipFields.has(field)) {
          return false;
        }
        if (includeFields.has(field)) {
          return true;
        }
        const value = props.item[field];
        return !isObject(value) && value && (!getField(field) || !getField(field).hideAttr);
      });

      // add geo_loc_name to after lat/lon
      if (props.item?.annotations?.geo_loc_name !== undefined) {
        const geoLocIndex = ret.includes('latitude') ? ret.indexOf('latitude') + 1 : ret.length;
        ret.splice(geoLocIndex, 0, 'geo_loc_name');
      }

      if (props.item?.annotations?.biosample_categories !== null) {
        ret.push('biosample_categories');
      }

      return ret;
    });

    const relatedBiosamples = computed(() => {
      const relatedBiosampleIds = new Set();
      if (props.type !== 'biosample') {
        return relatedBiosampleIds;
      }
      const biosample = props.item as BiosampleSearchResult;
      if (biosample.omics_processing.length) {
        biosample.omics_processing.forEach((omicsProcessing: any) => {
          if (omicsProcessing.biosample_inputs) {
            omicsProcessing.biosample_inputs.forEach((biosampleInput: BiosampleSearchResult) => {
              if (biosampleInput.id && biosampleInput.id !== biosample.id) {
                relatedBiosampleIds.add(biosampleInput.id);
              }
            });
          }
        });
      }
      return relatedBiosampleIds;
    });

    const alternateIdentifiers = computed(() => props.item.alternate_identifiers
      .map((id) => ({ name: id, target: `https://identifiers.org/${id}` })));
    return {
      // computed
      alternateIdentifiers,
      displayFields,
      relatedBiosamples,
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
    <v-list v-if="alternateIdentifiers.length > 0 || item.emsl_biosample_identifiers.length > 0">
      <div class="display-1">
        Alternative Identifiers
      </div>
      <AttributeItem
        v-for="({ name, target }) in alternateIdentifiers"
        :key="name"
        v-bind="{ item, field, link: { name, target } }"
      />
      <AttributeItem
        v-for="emslId, index in item.emsl_biosample_identifiers"
        :key="emslId"
        v-bind="{ item, field: 'emsl_biosample_identifiers', index, displayName: 'EMSL Identifier' }"
      />
    </v-list>
    <v-list v-if="type === 'biosample' && relatedBiosamples.size">
      <div class="display-1">
        Related Biosamples
      </div>
      <v-list-item
        v-for="biosampleId in relatedBiosamples"
        :key="biosampleId"
        :href="'/details/sample/' + biosampleId"
      >
        <v-list-item-avatar>
          <v-icon>mdi-link</v-icon>
        </v-list-item-avatar>
        <v-list-item-content>
          <v-list-item-title>
            ID
          </v-list-item-title>
          <v-list-item-subtitle>
            {{ biosampleId }}
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </div>
</template>
