<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  toRef,
  ref,
  watch,
  nextTick,
} from 'vue';
import { DataTableHeader } from 'vuetify';
import {
  Condition, entityType, KeggTermSearchResponse,
} from '@/data/api';
import {
  keggEncode, GeneFunctionSearchParams,
} from '@/encoding';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import useRequest from '@/use/useRequest';
import { computedAsync } from '@vueuse/core';

export type GeneType = 'kegg' | 'cog' | 'pfam' | 'go';

export default defineComponent({

  props: {
    conditions: {
      type: Array as PropType<Condition[]>,
      required: true,
    },
    geneTypeParams: {
      type: Object as PropType<GeneFunctionSearchParams>,
      required: true,
    },
    geneType: {
      type: String as PropType<GeneType>,
      default: 'kegg', // can be kegg, cog, or pfam
    },
  },
  emits: ['select'],
  setup(props, { emit }) {
    const selected = ref<string | null>(null);
    const conditions = toRef(props, 'conditions');
    const field = ref('id');
    const table = computed(() => {
      const typeToTable: Record<GeneType, entityType> = {
        kegg: 'kegg_function',
        cog: 'cog_function',
        pfam: 'pfam_function',
        go: 'go_function',
      };
      return typeToTable[props.geneType];
    });
    const { myConditions } = useFacetSummaryData({ conditions, field, table });

    /** Autocomplete state */
    const { loading, request } = useRequest();
    const search = ref('');

    async function geneSearch(): Promise<KeggTermSearchResponse[]> {
      return request(() => props.geneTypeParams.searchFunction(search.value || ''));
    }

    async function getGeneResults() {
      const resp = await geneSearch();
      const results = resp
        .map((v: KeggTermSearchResponse) => ({ text: getTermDisplayText(v.term, v.text), value: v.term }));
      if (results.length === 0 && search.value && props.geneTypeParams.searchWithInputText(search.value)) {
        results.push({ value: search.value, text: search.value });
      }
      return results;
    }

    const items = computedAsync(
      async () => {
        return getGeneResults();
      },
      [] as { text: string; value: string }[],
    );

    function getTermDisplayText(term: string, text: string) {
      if (text) {
        return `${term}: ${text}`;
      }
      return term;
    }

    function setSearch(val: string) {
      search.value = val;
    }

    watch(search, async () => {
      items.value = await getGeneResults();
    });

    const headers: DataTableHeader[] = [
      {
        title: 'Term',
        value: 'value',
        width: '300',
        sortable: true,
      },
      {
        title: 'Remove',
        value: 'remove',
        sortable: false,
        width: 90,
      },
    ];

    function addTerm(term: string) {
      if (!term) return;
      const newConditions = [...conditions.value, {
        op: '==',
        field: field.value,
        value: props.geneTypeParams.encodeFunction(term, false),
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
      setSearch,
    };
  },
});
</script>

<template>
  <div class="match-list-table">
    <v-row no-gutters>
      <div class="px-4 text-caption">
        <p>
          {{ geneTypeParams.description }}
        </p>
        <p v-if="geneTypeParams.expectedFormats">
          Expected formats: <code>{{ geneTypeParams.expectedFormats }}</code>
        </p>
        <p class="text-subtitle-2">
          More information at <a :href="geneTypeParams.helpSite">{{ geneTypeParams.helpSite }}</a>
        </p>
      </div>
      <slot name="subtitle" />
      <v-autocomplete
        v-model="selected"
        :loading="loading"
        :items="items"
        item-title="text"
        item-value="value"
        :label="geneTypeParams.label"
        clearable
        class="px-3 grow"
        density="compact"
        hide-details
        variant="outlined"
        flat
        @update:model-value="addTerm"
        @update:search="setSearch"
      />
    </v-row>
    <v-data-table
      density="compact"
      height="355px"
      :items-per-page="10"
      :item-key="'facet'"
      :items="myConditions"
      :headers="headers"
    >
      <template #[`item.value`]="{ item }">
        <a :href="geneTypeParams.encodeFunction(item.value as string, true)">
          {{ item.value }}
        </a>
      </template>
      <template #[`item.remove`]="{ item }">
        <v-btn
          size="x-small"
          depr
          color="error"
          @click="removeTerm(item.value as string)"
        >
          remove
        </v-btn>
      </template>
    </v-data-table>
  </div>
</template>
