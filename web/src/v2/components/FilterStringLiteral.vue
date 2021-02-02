<script lang="ts">
import { Condition, entityType } from '@/data/api';
import {
  defineComponent, PropType, toRef, ref,
} from '@vue/composition-api';
import { fieldDisplayName } from '@/util';
import { getField } from '@/encoding';
import useFacetSummaryData from '@/v2/use/useFacetSummaryData';
import { DataTableHeader } from 'vuetify';

export default defineComponent({

  props: {
    field: {
      type: String,
      required: true,
    },
    table: {
      type: String as PropType<entityType>,
      required: true,
    },
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },

  setup(props, { emit }) {
    const searchTerm = ref('');
    const conditions = toRef(props, 'conditions');
    const field = toRef(props, 'field');
    const table = toRef(props, 'table');
    const { myConditions } = useFacetSummaryData({ conditions, field, table });

    const headers: DataTableHeader[] = [
      {
        text: fieldDisplayName(props.field, props.table),
        value: 'value',
        width: '300',
        sortable: true,
      },
      {
        text: 'Remove',
        value: 'remove',
        sortable: false,
        width: 90,
        filterable: false,
      },
    ];

    function setSelected({ facet, value }: {
      facet: string; value: boolean;
    }) {
      const encode = getField(props.field, props.table)?.encode;
      let newConditions;
      if (value) {
        newConditions = [...conditions.value, {
          op: '==',
          field: field.value,
          value: encode ? encode(facet) : facet,
          table: table.value,
        }];
        searchTerm.value = '';
      } else {
        newConditions = conditions.value
          .filter((c) => !(
            c.field === field.value
            && c.value === facet
            && c.table === table.value
          ));
      }
      emit('select', { conditions: newConditions });
    }

    return {
      headers,
      myConditions,
      searchTerm,
      setSelected,
    };
  },
});
</script>

<template>
  <div class="match-list-table">
    <v-row
      no-gutters
      class="my-3"
    >
      <v-text-field
        v-model="searchTerm"
        solo
        :label="field"
        clearable
        class="px-3 grow"
        dense
        hide-details
        outlined
        flat
      />
      <v-btn
        fab
        depressed
        small
        color="primary"
        class="ml-1 mr-4 "
        @click="setSelected({ facet: searchTerm, value: true })"
      >
        <v-icon>mdi-plus</v-icon>
      </v-btn>
    </v-row>
    <v-data-table
      dense
      height="355px"
      :items-per-page="10"
      :item-key="'facet'"
      :items="myConditions"
      :headers="headers"
    >
      <template v-slot:item.remove="{ item }">
        <v-btn
          small
          depressed
          color="error"
          @click="setSelected({ facet: item.value, value: false })"
        >
          remove
        </v-btn>
      </template>
    </v-data-table>
  </div>
</template>

<style lang="scss">
.match-list-table {
  .v-data-table {
    table {
      table-layout: fixed;
    }

    td {
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }
}
</style>
