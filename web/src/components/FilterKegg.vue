<script lang="ts">
import {
  defineComponent, PropType, toRef, ref, watch, nextTick,
} from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { Condition, entityType, api, KeggTermSearchResponse } from '@/data/api';
import { keggEncode, stringIsKegg } from '@/encoding';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import useRequest from '@/use/useRequest';

export default defineComponent({

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    geneType: {
      type: String,
      default: 'kegg', // can be kegg, cog, or pfam
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

    /** Change based on gene type */
    const description: Ref<string> = ref('');
    const expectedFormats: Ref<string> = ref('');

    function description(): string {
      switch (props.geneType) {
        case 'kegg':
          return request(() => api.keggSearch(search.value || ''));
        case 'cog':
        case 'pfam':
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
    }

    async function geneSearch(): Promise<KeggTermSearchResponse[]> {
      switch (props.geneType) {
        case 'kegg':
          return request(() => api.keggSearch(search.value || ''));
        case 'cog':
        case 'pfam':
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
    }

    watch(search, async () => {
      // MLN change this to be non-kegg specific
      const resp = (await geneSearch())
        .map((v: KeggTermSearchResponse) => ({ text: `${v.term}: ${v.text}`, value: v.term }));
      if (resp.length === 0 && search.value && stringIsKegg(search.value)) {
        resp.push({ value: search.value, text: search.value });
      }
      items.value = resp;
    });

    const headers: DataTableHeader[] = [
      {
        // MLN change from KEGG
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
      // MLN change from KEGG
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
        <p>
          <!-- MLN KEGG-specific stuff -->
          {{ description }}
          KEGG Gene Function search filters results to
          samples that have at least one of the chosen KEGG terms.
          Orthology, Module, and Pathway are supported.
          Expected formats: <code>K00000, M00000, map00000, ko00000, rn00000, and ec00000</code>
        </p>
        <p class="text-subtitle-2">
          More information at <a href="https://www.genome.jp/kegg/">genome.jp/kegg</a>
        </p>
      </div>
      <slot name="subtitle" />
      <!-- MLN change this label -->
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
        <!-- MLN change this -->
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
