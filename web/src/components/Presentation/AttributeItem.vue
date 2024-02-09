<script lang="ts">
import { defineComponent, PropType } from '@vue/composition-api';
import { getField } from '@/encoding';
import { fieldDisplayName, valueDisplayName } from '@/util';
import { BaseSearchResult, BiosampleSearchResult, JSONValue } from '@/data/api';

export enum Format {
  RangeWithUnit = 'RangeWithUnit',
  Range = 'Range',
  Unit = 'Unit',
}

/**
 * Helper function that returns a string representation of the depth in the specified format, if the specified
 * depth annotation contains adequate information to do so. Otherwise, the function returns `undefined`.
 */
const buildStrFromDepthAnnotation = (depthAnnotation: JSONValue, format: Format): string | undefined => {
  let str: string | undefined;

  // Regardless of the specified format, check whether the depth annotation is a "non-null, non-array" object.
  if (typeof depthAnnotation === 'object' && depthAnnotation !== null && !Array.isArray(depthAnnotation)) {
    // Extract data according to the specified format.
    switch (format) {
      case Format.RangeWithUnit: {
        const { has_minimum_numeric_value, has_maximum_numeric_value, has_unit } = depthAnnotation;
        if (typeof has_minimum_numeric_value === 'number' && typeof has_maximum_numeric_value === 'number' && typeof has_unit === 'string') {
          str = `${has_minimum_numeric_value} - ${has_maximum_numeric_value} ${has_unit}`;
        }
        break;
      }
      case Format.Range: {
        const { has_minimum_numeric_value, has_maximum_numeric_value } = depthAnnotation;
        if (typeof has_minimum_numeric_value === 'number' && typeof has_maximum_numeric_value === 'number') {
          str = `${has_minimum_numeric_value} - ${has_maximum_numeric_value}`;
        }
        break;
      }
      case Format.Unit: {
        const { has_unit } = depthAnnotation;
        if (typeof has_unit === 'string') {
          str = has_unit;
        }
        break;
      }
      default: {
        break;
      }
    }
  }

  return str;
};

/**
 * Helper function that checks whether the specified depth annotation describes a range.
 */
export const doesDepthAnnotationDescribeRange = (depthAnnotation: JSONValue): boolean => {
  const rangeWithUnit = buildStrFromDepthAnnotation(depthAnnotation, Format.RangeWithUnit);
  const range = buildStrFromDepthAnnotation(depthAnnotation, Format.Range);
  return typeof rangeWithUnit === 'string' || typeof range === 'string';
};

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<BaseSearchResult | BiosampleSearchResult>,
      required: true,
    },
    field: {
      type: String,
      required: true,
    },
    index: {
      type: Number,
      required: false,
      default: -1,
    },
    link: {
      type: Object as PropType<{ name: string; target: string; } | null>,
      default: null,
    },
    bindClick: {
      type: Boolean,
      default: false,
    },
    image: {
      type: String,
      default: '',
    },
    displayName: {
      type: String,
      required: false,
      default: '',
    },
  },

  setup(props) {
    function getValue(field: string) {
      if (field === 'depth') {
        const topLevelDepth = props.item.depth;

        // Use the top-level depth value as the fallback result.
        let result = topLevelDepth;

        // Check whether there is a depth annotation.
        if ('depth' in props.item.annotations) {
          const depthAnnotation = props.item.annotations.depth as JSONValue;
          // Check whether the depth annotation describes a range with a unit;
          // and, if so, use that as the result.
          const rangeWithUnitStr = buildStrFromDepthAnnotation(depthAnnotation, Format.RangeWithUnit);
          if (typeof rangeWithUnitStr === 'string') {
            result = rangeWithUnitStr;
          } else {
            // Check whether the depth annotation describes a range;
            // and, if so, use that as the result.
            const rangeStr = buildStrFromDepthAnnotation(depthAnnotation, Format.Range);
            if (typeof rangeStr === 'string') {
              result = rangeStr;
            } else {
              // Check whether the top-level depth value is numeric (not null) and the depth annotation contains a unit;
              // and, if so, use a concatenation of the two as the result.
              const unitStr = buildStrFromDepthAnnotation(depthAnnotation, Format.Unit);
              if (typeof topLevelDepth === 'number' && typeof unitStr === 'string') {
                result = `${topLevelDepth} ${unitStr}`;
              }
            }
          }
        }

        return result;
      }
      if (field === 'geo_loc_name') {
        return props.item.annotations.geo_loc_name;
      }
      if (field === 'biosample_categories') {
        return (props.item?.annotations.biosample_categories as string[]).join(', ');
      }
      if (
        field === 'env_broad_scale'
          || field === 'env_local_scale'
          || field === 'env_medium'
      ) {
        const item = props.item as BiosampleSearchResult;
        const env = item[field];
        return `${env.label} (${env.id})`;
      }
      if (field === 'emsl_biosample_identifiers') {
        const item = props.item as BiosampleSearchResult;
        return item.emsl_biosample_identifiers[props.index] || '';
      }
      return valueDisplayName(field, props.item[field]);
    }

    function href(field: string) {
      if (field.startsWith('open_in_')) {
        return props.item[field];
      }
      const value = props.item[field] as string;
      if (typeof value === 'string' && value.startsWith('http')) {
        return props.item[field];
      }
      if (field === 'study_id') {
        return `/details/study/${props.item.study_id}`;
      }
      return undefined;
    }

    return {
      getField,
      fieldDisplayName,
      getValue,
      href,
    };
  },
});
</script>

<template>
  <v-list-item
    v-if="link"
    :key="link.name"
    :href="link.target"
  >
    <img
      v-if="image"
      :src="image"
      width="160px"
      class="pr-2"
      alt="Logo"
    >
    <v-list-item-avatar v-else>
      <v-icon>mdi-link</v-icon>
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title>
        {{ link.name }}
      </v-list-item-title>
      <v-list-item-subtitle>
        {{ link.target }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
  <v-list-item
    v-else
    :href="href(field)"
    :target="field==='study_id' ? '' : '_blank' "
    rel="noopener noreferrer"
    v-on="{
      // TODO: fix warning.
      click: bindClick ? () => $emit('click') : undefined
    }"
  >
    <img
      v-if="image"
      :src="image"
      width="160px"
      class="pr-2"
      alt="Logo"
    >
    <v-list-item-avatar v-else-if="getField(field)">
      <v-icon>
        {{ getField(field).icon || 'mdi-text' }}
      </v-icon>
    </v-list-item-avatar>
    <v-list-item-content>
      <v-list-item-title>
        {{ displayName.length > 0 ? displayName : fieldDisplayName(field) }}
      </v-list-item-title>
      <v-list-item-subtitle
        style="white-space: initial;"
      >
        {{ getValue(field) }}
      </v-list-item-subtitle>
    </v-list-item-content>
  </v-list-item>
</template>
