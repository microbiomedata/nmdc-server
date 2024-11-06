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
  Condition, entityType, api, KeggTermSearchResponse,
} from '@/data/api';
import {
  keggEncode,
  stringIsKegg,
  cogEncode,
  pfamEncode,
  geneFunctionType,
  GeneFunctionSearchParams,
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

    /** Change based on gene type */
    const description = computed(() => {
      switch (props.geneType) {
        case 'kegg':
          return 'KEGG Gene Function search filters results to '
          + 'samples that have at least one of the chosen KEGG terms. '
          + 'Orthology, Module, and Pathway are supported.';
        case 'cog':
          return 'COG Gene Function search filters results to '
          + 'samples that have at least one of the chosen COG terms. '
          + 'Term, Function, and Pathway are supported.';
        case 'pfam':
          return 'Pfam Gene Function search filters results to '
          + 'samples that have at least one of the chosen Pfam terms. '
          + 'Accession and Clan are supported.';
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
    });

    const helpSite = computed(() => {
      const sites: Record<geneFunctionType, string> = {
        kegg: 'https://wwwigenome.jp/kegg/',
        cog: 'https://www.ncbi.nlm.nih.gov/research/cog/',
        pfam: 'https://www.ebi.ac.uk/interpro/set/all/entry/pfam/',
      };
      return sites[props.geneType as geneFunctionType];
    });

    const expectedFormats = computed(() => {
      switch (props.geneType) {
        case 'kegg':
          return 'K00000, M00000, map00000, ko00000, rn00000, and ec00000';
        case 'cog':
          return 'COG0000';
        case 'pfam':
          return 'PF00000, CL0000';
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
    });

    const label = computed(() => {
      let readableType = '';
      switch (props.geneType) {
        case 'kegg':
          readableType = 'KEGG';
          break;
        case 'cog':
          readableType = 'COG';
          break;
        case 'pfam':
          readableType = 'PFAM';
          break;
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
      return `Search for ${readableType} terms`;
    });

    async function geneSearch(): Promise<KeggTermSearchResponse[]> {
      switch (props.geneType) {
        case 'kegg':
          return request(() => api.keggSearch(search.value || ''));
        case 'cog':
          return request(() => api.cogSearch(search.value || ''));
        case 'pfam':
          return request(() => api.pfamSearch(search.value || ''));
        default:
          throw new Error(`Unexpected gene type: ${props.geneType}`);
      }
    }

    const encodeFunctionMap: Record<geneFunctionType, (val: string, url: boolean) => string> = {
      kegg: keggEncode,
      cog: cogEncode,
      pfam: pfamEncode,
    };

    function encode(value: string, url: boolean = false): string {
      console.log({ value, url });
      return encodeFunctionMap[props.geneType as geneFunctionType](value, url);
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
        value: encode(term),
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
      description,
      expectedFormats,
      label,
      encode,
      helpSite,
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
          {{ description }}
        </p>
        <p v-if="expectedFormats">
          Expected formats: <code>{{ expectedFormats }}</code>
        </p>
        <p class="text-subtitle-2">
          More information at <a :href="helpSite">{{ helpSite }}</a>
        </p>
      </div>
      <slot name="subtitle" />
      <!-- MLN change this label -->
      <v-autocomplete
        v-model="selected"
        :loading="loading"
        :items="items"
        :search-input.sync="search"
        :label="label"
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
        <a :href="encode(item.value, true)">
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
