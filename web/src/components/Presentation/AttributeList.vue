<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';
import { isObject } from 'lodash';

import { BaseSearchResult, BiosampleSearchResult } from '@/data/api';
import { getField } from '@/encoding';
// @ts-ignore
import { formatBiosampleDepth } from '@/util';
import gold from '@/assets/GOLD.png';
import img from '@/assets/IMG.png';
import emsl from '@/assets/EMSL.png';
import AttributeItem from './AttributeItem.vue';
import PageSection from '@/views/IndividualResults/PageSection.vue';

export default defineComponent({
  components: {PageSection, AttributeItem },

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

        // For the "depth" field, we only include it if it is something we can format as a string.
        // Note: I assert some types here to work around the inaccurate type definitions in `api.ts`.
        if (field === 'depth') {
          const formattedDepth = formatBiosampleDepth(props.item.annotations?.depth as object | null, props.item.depth as number | null);
          return formattedDepth !== null;
        }

        const value = props.item[field];
        return !isObject(value) && value && (!getField(field) || !getField(field).hideAttr);
      });

      // add geo_loc_name to after lat/lon
      if (props.item?.annotations?.geo_loc_name !== undefined) {
        const geoLocIndex = ret.includes('latitude') ? ret.indexOf('latitude') + 1 : ret.length;
        ret.splice(geoLocIndex, 0, 'geo_loc_name');
      }

      if (props.item?.annotations?.biosample_categories !== undefined) {
        ret.push('biosample_categories');
      }

      return ret;
    });

    const relatedBiosamples = computed(() => {
      const relatedBiosampleIds = new Set();
      const relatedBiosampleInfo: any[] | Set<unknown> = [];
      if (props.type !== 'biosample') {
        return relatedBiosampleIds;
      }
      const biosample = props.item as BiosampleSearchResult;
      if (biosample.omics_processing.length) {
        biosample.omics_processing.forEach((omicsProcessing: any) => {
          if (omicsProcessing.biosample_inputs) {
            omicsProcessing.biosample_inputs.forEach((biosampleInput: BiosampleSearchResult) => {
              if (biosampleInput.id && biosampleInput.id !== biosample.id) {
                if (!relatedBiosampleIds.has(biosampleInput.id)) {
                  relatedBiosampleInfo.push({ id: biosampleInput.id, name: biosampleInput.name });
                  relatedBiosampleIds.add(biosampleInput.id);
                }
              }
            });
          }
        });
      }
      return relatedBiosampleInfo;
    });

    const alternateIdentifiers = computed(() => props.item.alternate_identifiers
      .map((id) => ({ name: id, target: `https://identifiers.org/${id}` })));
    return {
      // computed
      alternateIdentifiers,
      displayFields,
      relatedBiosamples,
      gold,
      img,
      emsl,
    };
  },
});
</script>

<template>
  <div>
    <PageSection heading="Attributes">
      <v-list class="attribute-grid">
        <div
          v-for="field in displayFields"
          :key="field"
          class="mb-2"
        >
          <AttributeItem v-bind="{ item, field }" />
        </div>
      </v-list>
    </PageSection>

    <PageSection
      v-if="alternateIdentifiers.length > 0 || Array.isArray(item.emsl_biosample_identifiers) && item.emsl_biosample_identifiers.length > 0"
      heading="Alternative Identifiers"
    >
      <v-list class="pa-0">
        <AttributeItem
          v-for="({ name, target }) in alternateIdentifiers"
          class="mb-2"
          :key="name"
          v-bind="{ item, link: { name, target } }"
          :image="name.startsWith('gold') ? gold : name.startsWith('img') ? img : ''"
        />
        <AttributeItem
          v-for="emslId, index in item.emsl_biosample_identifiers"
          class="mb-2"
          :key="emslId"
          v-bind="{ item, field: 'emsl_biosample_identifiers', index, displayName: 'EMSL Identifier' }"
          :image="emsl"
        />
      </v-list>
    </PageSection>

    <PageSection
      v-if="type === 'biosample' && Array.isArray(relatedBiosamples) && relatedBiosamples.length > 0"
      heading="Related Biosamples"
    >
      <v-list class="pa-0">
        <v-list-item
          v-for="biosample in relatedBiosamples"
          :key="biosample.id"
          class="mb-2"
          :href="'/details/sample/' + biosample.id"
        >
          <template #prepend>
            <v-icon>mdi-link</v-icon>
          </template>
          <v-list-item-title>
            {{ biosample.name }}
          </v-list-item-title>
          <v-list-item-subtitle>
            ID: {{ biosample.id }}
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </PageSection>
  </div>
</template>

<style scoped>
.attribute-grid {
  /* This does not use display: grid because we want a specific number of columns,
     but with items that flow from top-to-bottom first then left-to-right. */
  column-count: 3;
  column-gap: 8px;
  padding: 0;
}
</style>
