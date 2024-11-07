<script lang="ts">
import {
  computed,
  defineComponent,
  PropType,
  toRef,
  ref,
  watch,
  nextTick,
} from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import {
  Condition, entityType, KeggTermSearchResponse,
} from '@/data/api';
import {
  keggEncode, stringIsKegg, GeneFunctionSearchParams,
} from '@/encoding';
import useFacetSummaryData from '@/use/useFacetSummaryData';
import useRequest from '@/use/useRequest';

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
      type: String,
      default: 'kegg', // can be kegg, cog, or pfam
    },
  },

  setup(props, { emit }) {
    const selected = ref(null);
    const conditions = toRef(props, 'conditions');
    const field = ref('id');
    const table = computed(() => {
      const typeToTable: Record<string, entityType> = {
        kegg: 'kegg_function',
        cog: 'cog_function',
        pfam: 'pfam_function',
      };
      return typeToTable[props.geneType];
    });
    const { myConditions } = useFacetSummaryData({ conditions, field, table });

    /** Autocomplete state */
    const { loading, request } = useRequest();
    const items = ref([] as { text: string; value: string }[]);
    const search = ref('');

    async function geneSearch(): Promise<KeggTermSearchResponse[]> {
      return request(() => props.geneTypeParams.searchFunction(search.value || ''));
    }

    watch(search, async () => {
      const resp = (await geneSearch())
        .map((v: KeggTermSearchResponse) => ({ text: `${v.term}: ${v.text}`, value: v.term }));
      if (resp.length === 0 && search.value && stringIsKegg(search.value)) {
        resp.push({ value: search.value, text: search.value });
      }
      items.value = resp;
    });

    const headers: DataTableHeader[] = [
      {
        text: 'Term',
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
        :search-input.sync="search"
        :label="geneTypeParams.label"
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
        <a :href="geneTypeParams.encodeFunction(item.value, true)">
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
