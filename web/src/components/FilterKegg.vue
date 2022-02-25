<script lang="ts">
import {
  defineComponent, PropType, toRef, ref, watch, nextTick,
} from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { Condition, entityType, api } from '@/data/api';
import { keggEncode, stringIsKegg } from '@/encoding';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import useRequest from '@/use/useRequest';

export default defineComponent({

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
  },

  setup(props, { emit }) {
    const selected = ref(null);
    const conditions = toRef(props, 'conditions');
    const field = ref('id');
    const table = ref('gene_function' as entityType);
    const { myConditions } = useFacetSummaryData({ conditions, field, table });

    /** Autocomplete state */
    const { loading, request } = useRequest();
    const items = ref([] as { text: string; value: string }[]);
    const search = ref('');

    watch(search, async () => {
      const resp = (await request(() => api.keggSearch(search.value || '')))
        .map((v) => ({ text: `${v.term}: ${v.text}`, value: v.term }));
      if (resp.length === 0 && search.value && stringIsKegg(search.value)) {
        resp.push({ value: search.value, text: search.value });
      }
      items.value = resp;
    });

    const headers: DataTableHeader[] = [
      {
        text: 'Kegg Term',
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

    function addTerm(term: string) {
      if (!term) return;
      const newConditions = [...conditions.value, {
        op: '==',
        field: field.value,
        value: keggEncode(term),
        table: table.value,
      }];
      emit('select', { conditions: newConditions });
      nextTick().then(() => { selected.value = null; });
    }

    function removeTerm(term: string) {
      const newConditions = conditions.value
        .filter((c) => !(
          c.field === field.value
          && c.value === term
          && c.table === table.value
        ));
      emit('select', { conditions: newConditions });
    }

    return {
      field,
      table,
      headers,
      myConditions,
      /* Autocomplete */
      loading,
      search,
      items,
      selected,
      keggEncode,
      addTerm,
      removeTerm,
    };
  },
});
</script>

<template>
  <div class="match-list-table">
    <v-row no-gutters>
      <div class="px-4 text-caption">
        <p class="text-subtitle-2">
          KEGG search is currently only available for metagenome data.
        </p>
        <p>
          KEGG Gene Function search filters results to
          samples that have at least one of the chosen KEGG terms.
          Orthology, Pathway, and Module are supported.
          Expected format: <code>K00000, M00000 or MAP00000</code>
        </p>
        <p class="text-subtitle-2">
          More information at <a href="https://www.genome.jp/kegg/">genome.jp/kegg</a>
        </p>
      </div>
      <slot name="subtitle" />
      <v-autocomplete
        v-model="selected"
        :loading="loading"
        :items="items"
        :search-input.sync="search"
        label="Search for KEGG terms"
        clearable
        class="px-3 grow"
        dense
        hide-details
        outlined
        flat
        @change="addTerm"
      />
    </v-row>
    <v-data-table
      dense
      height="355px"
      :items-per-page="10"
      :item-key="'facet'"
      :items="myConditions"
      :headers="headers"
    >
      <template #[`item.value`]="{ item }">
        <a :href="keggEncode(item.value, true)">
          {{ item.value }}
        </a>
      </template>
      <template #[`item.remove`]="{ item }">
        <v-btn
          x-small
          depr
          color="error"
          @click="removeTerm(item.value)"
        >
          remove
        </v-btn>
      </template>
    </v-data-table>
  </div>
</template>
