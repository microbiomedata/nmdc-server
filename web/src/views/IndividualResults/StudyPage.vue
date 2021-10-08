<script lang="ts">
import {
  computed, defineComponent, reactive, watchEffect, ref, watch,
} from '@vue/composition-api';

import { isObject } from 'lodash';
// @ts-ignore
import Cite from 'citation-js';
import {
  typeWithCardinality, valueCardinality, fieldDisplayName,
} from '@/util';
import { api, StudySearchResults } from '@/data/api';
import { setUniqueCondition } from '@/store';
import { useRouter } from '@/use/useRouter';
import Attribute from '@/components/Presentation/Attribute.vue';
import IndividualTitle from '@/views/IndividualResults/IndividualTitle.vue';
import InvestigatorBio from '@/components/InvestigatorBio.vue';
/**
 * Override citations for certain DOIs
 */
const CitationOverrides = {
  'https://doi.org/10.46936/10.25585/60000017': 'Doktycz, M. (2020) BioScales - Defining plant gene function and its connection to ecosystem nitrogen and carbon cycling [Data set]. DOE Joint Genome Institute. https://doi.org/10.46936/10.25585/60000017',
};

export default defineComponent({
  props: {
    id: {
      type: String,
      required: true,
    },
  },

  components: {
    Attribute,
    IndividualTitle,
    InvestigatorBio,
  },

  setup(props) {
    const data = reactive({
      doiCitation: '' as string | null,
      publications: [] as any[],
    });

    const item = ref(null as StudySearchResults | null);

    watchEffect(() => {
      api.getStudy(props.id).then((b) => { item.value = b; });
    });

    const displayFields = computed(() => {
      if (item.value === null) {
        return [];
      }
      return Object.entries(item.value).filter(([field, value]) => {
        if (['name', 'description'].includes(field)) {
          return false;
        }
        return !isObject(value);
      });
    });

    function relatedTypeDescription(relatedType: string) {
      if (item.value) {
        const n = valueCardinality(item.value[`${relatedType}_id`]);
        return `${n} ${typeWithCardinality(relatedType, n)}`;
      }
      return '';
    }

    function openLink(url: string) {
      window.open(url, '_blank');
    }

    function formatAPA(citation: any) {
      return citation.format('bibliography', {
        format: 'text',
        template: 'apa',
        lang: 'en-US',
      });
    }

    const router = useRouter();

    function setChecked(omicsType: string = '') {
      setUniqueCondition(
        ['study_id', 'omics_type'],
        ['study', 'omics_processing'], [{
          value: props.id,
          table: 'study',
          op: '==',
          field: 'study_id',
        }, {
          value: omicsType,
          table: 'omics_processing',
          field: 'omics_type',
          op: '==',
        }],
      );
      /* @ts-ignore */
      router.go(-1);
    }

    watch(item, async (_item) => {
      const publicationDoiInfo = _item?.publication_doi_info;
      if (publicationDoiInfo) {
        data.doiCitation = null;
        data.publications = [];
        const unformattedPublications = Object.values(publicationDoiInfo);

        [data.doiCitation] = unformattedPublications
          .filter((c) => c.type === 'dataset' && c.type)
          .map((c) => formatAPA(new Cite(c)));
        data.publications = unformattedPublications
          .filter((c) => c.type !== 'dataset' && c.type)
          .map((c) => formatAPA(new Cite(c)));
      }
    });

    return {
      CitationOverrides,
      data,
      item,
      displayFields,
      /* Methods */
      setChecked,
      relatedTypeDescription,
      openLink,
      formatAPA,
      typeWithCardinality,
      fieldDisplayName,
    };
  },
});
</script>

<template>
  <v-container fluid>
    <v-main v-if="item !== null">
      <v-row>
        <v-col cols="7">
          <IndividualTitle :item="item">
            <template #default>
              <div v-if="item.omics_processing_counts">
                <template v-for="item in item.omics_processing_counts">
                  <v-chip
                    v-if="item.count && (item.type.toLowerCase() !== 'lipidomics')"
                    :key="item.type"
                    small
                    class="mr-2 my-1"
                    @click="setChecked(item.type)"
                  >
                    {{ fieldDisplayName(item.type) }}: {{ item.count }}
                  </v-chip>
                </template>
              </div>
              <div v-else>
                <v-chip
                  small
                  disabled
                  class="my-1"
                >
                  Omics data coming soon
                </v-chip>
              </div>
            </template>
          </IndividualTitle>
          <InvestigatorBio :item="item" />
          <v-col offset="1">
            <div class="display-1">
              Study Details
            </div>
            <v-list>
              <Attribute v-bind="{ item, field: 'doi' }" />
              <Attribute v-bind="{ item, field: 'id' }" />
              <Attribute v-bind="{ item, field: 'funding_sources' }" />
              <Attribute v-bind="{ item, field: 'sample_count' }" />
            </v-list>
            <div class="display-1">
              External Resources
            </div>
            <v-list>
              <v-list-item>
                <v-list-item-avatar>
                  <v-icon>mdi-file-document</v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title class="text-h6">
                    Additional data
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <Attribute
                style="padding-left: 60px;"
                v-bind="{ item, field: 'open_in_gold' }"
              />
              <v-list-item v-if="item.relevant_protocols">
                <v-list-item-avatar>
                  <v-icon>mdi-file-document</v-icon>
                </v-list-item-avatar>
                <v-list-item-content>
                  <v-list-item-title class="text-h6">
                    Protocols
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              <template
                v-for="proto in (item.relevant_protocols || [])"
              >
                <Attribute
                  :key="proto"
                  style="padding-left: 60px;"
                  v-bind="{
                    item,
                    link: { name: proto, target: proto},
                    field: 'relevant_protocols' }
                  "
                />
              </template>
            </v-list>
          </v-col>
        </v-col>
        <v-col cols="5">
          <div class="ma-4 pa-2 grey lighten-4">
            <v-subheader>Dataset Citation</v-subheader>
            <v-list class="transparent">
              <v-divider />
              <v-list-item>
                <v-list-item-content
                  v-text="data.doiCitation || CitationOverrides[item.doi] || item.doi"
                />
                <v-list-item-action>
                  <v-tooltip top>
                    <template v-slot:activator="{ on }">
                      <v-btn
                        icon
                        v-on="on"
                        @click="openLink(`https://doi.org/${item.doi}`)"
                      >
                        <v-icon>mdi-open-in-new</v-icon>
                      </v-btn>
                    </template>
                    <span>Visit site</span>
                  </v-tooltip>
                </v-list-item-action>
              </v-list-item>
            </v-list>
            <v-subheader v-if="data.publications.length > 0">
              Other publications
            </v-subheader>
            <v-list class="transparent">
              <template v-for="(pub, pubIndex) in data.publications">
                <v-divider :key="`${pubIndex}-divider`" />
                <v-list-item :key="pubIndex">
                  <v-list-item-content v-text="pub" />
                  <v-list-item-action>
                    <v-tooltip top>
                      <template v-slot:activator="{ on }">
                        <v-btn
                          icon
                          v-on="on"
                          @click="openLink(`https://doi.org/${item.publication_dois[pubIndex]}`)"
                        >
                          <v-icon>mdi-open-in-new</v-icon>
                        </v-btn>
                      </template>
                      <span>Visit site</span>
                    </v-tooltip>
                  </v-list-item-action>
                </v-list-item>
              </template>
            </v-list>
          </div>
        </v-col>
      </v-row>
    </v-main>
  </v-container>
</template>
