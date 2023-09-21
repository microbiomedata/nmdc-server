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
import { api, StudySearchResults, DOI } from '@/data/api';
import { setUniqueCondition, setConditions } from '@/store';
import { useRouter } from '@/use/useRouter';
import AttributeItem from '@/components/Presentation/AttributeItem.vue';
import IndividualTitle from '@/views/IndividualResults/IndividualTitle.vue';
import InvestigatorBio from '@/components/InvestigatorBio.vue';
/**
 * Override citations for certain DOIs
 */
 interface CitationOverridesType {
  [key: string]: string;
}
const CitationOverrides: CitationOverridesType = {
  '10.46936/10.25585/60000017': 'Doktycz, M. (2020) BioScales - Defining plant gene function and its connection to ecosystem nitrogen and carbon cycling [Data set]. DOE Joint Genome Institute. https://doi.org/10.46936/10.25585/60000017',
};
const GoldStudyLinkBase = 'https://gold.jgi.doe.gov/study?id=';

export default defineComponent({

  components: {
    AttributeItem,
    IndividualTitle,
    InvestigatorBio,
  },

  props: {
    id: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const data = reactive({
      awardDois: [] as DOI[],
      publicationDois: [] as DOI[],
      datasetDois: [] as DOI[],
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

    const goldLinks = computed(() => {
      if (!item.value) {
        return [];
      }
      const links = new Set();
      if (item.value.open_in_gold) {
        links.add(item.value.open_in_gold);
      }
      if (item.value.gold_study_identifiers) {
        item.value.gold_study_identifiers.forEach((identifier: string) => {
          if (identifier.toLowerCase().startsWith('gold:')) {
            links.add(GoldStudyLinkBase + identifier.substring(5));
          }
        });
      }
      return links;
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

    function seeOmicsForStudy(omicsType = '') {
      setUniqueCondition(
        ['study_id', 'omics_type'],
        ['study', 'omics_processing'],
        [{
          value: props.id,
          table: 'study',
          op: '==',
          field: 'id',
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

    function seeStudyInContext() {
      setConditions([{
        op: '==',
        table: 'study',
        field: 'id',
        value: props.id,
      }], true);
    }

    watch(item, async (_item) => {
      const doiMap = _item?.doi_map;
      if (doiMap) {
        data.awardDois = [];
        data.publicationDois = [];
        data.datasetDois = [];
        data.awardDois = _item.award_dois
          .filter((doi) => doi.id in doiMap)
          .map((doi) => CitationOverrides[doi.id] || formatAPA(new Cite(doi.id)));
        data.publicationDois = _item.publication_dois
          .filter((doi) => doi.id in doiMap)
          .map((doi) => formatAPA(new Cite(doiMap[doi.id])));
      }
    });

    return {
      CitationOverrides,
      GoldStudyLinkBase,
      goldLinks,
      data,
      item,
      displayFields,
      /* Methods */
      seeOmicsForStudy,
      relatedTypeDescription,
      openLink,
      formatAPA,
      typeWithCardinality,
      fieldDisplayName,
      seeStudyInContext,
      images: {
        // eslint-disable-next-line global-require
        gold: require('@/assets/GOLD.png'),
        // eslint-disable-next-line global-require
        ess: require('@/assets/ESS.png'),
        // eslint-disable-next-line global-require
        massive: require('@/assets/massive.png'),
      },
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
                <template v-for="val in item.omics_processing_counts">
                  <v-chip
                    v-if="val.count && (val.type.toLowerCase() !== 'lipidomics')"
                    :key="val.type"
                    small
                    class="mr-2 my-1"
                    @click="seeOmicsForStudy(val.type)"
                  >
                    {{ fieldDisplayName(val.type) }}: {{ val.count }}
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
              <AttributeItem
                v-bind="{ item, field: 'id', bindClick: true }"
                @click="seeStudyInContext"
              />
              <AttributeItem v-bind="{ item, field: 'funding_sources' }" />
              <AttributeItem
                v-bind="{ item, field: 'sample_count', bindClick: true }"
                @click="seeStudyInContext"
              />
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
              <AttributeItem
                v-for="link in goldLinks"
                :key="link"
                style="padding-left: 60px;"
                v-bind="{
                  item,
                  link: {
                    name: 'Open in GOLD',
                    target: link
                  }
                }"
                :image="images.gold"
              />
              <AttributeItem
                v-for="dive_id in item.ess_dive_datasets"
                :key="dive_id"
                v-bind="{
                  item,
                  link: {
                    name: 'ESS DIVE Dataset',
                    target: `https://identifiers.org/${dive_id}`,
                  },
                }"
                style="padding-left: 60px;"
                :image="images.ess"
                @click="seeStudyInContext"
              />
              <AttributeItem
                v-for="massive_id in item.massive_study_identifiers"
                :key="massive_id"
                v-bind="{
                  item,
                  link: {
                    name: 'MassIVE Study',
                    target: `https://identifiers.org/${massive_id}`
                  },
                }"
                style="padding-left: 60px;"
                :image="images.massive"
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
                <AttributeItem
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
          <div
            v-if="Object.keys(item.doi_map).length !== 0"
            class="ma-4 pa-2 grey lighten-4"
          >
            <template v-if="item.award_dois.length > 0">
              <v-subheader>
                Award DOIs
              </v-subheader>
              <v-list
                class="transparent"
              >
                <v-divider />
                <v-list-item
                  v-for="(award, index) in data.awardDois"
                  :key="index"
                >
                  <v-list-item-content>
                    {{ award }}
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-tooltip top>
                      <template #activator="{ on }">
                        <v-btn
                          icon
                          v-on="on"
                          @click="openLink(`https://doi.org/${item.award_dois[index].id}`)"
                        >
                          <v-icon>mdi-open-in-new</v-icon>
                        </v-btn>
                      </template>
                      <span>Visit site</span>
                    </v-tooltip>
                  </v-list-item-action>
                </v-list-item>
              </v-list>
            </template>
            <template
              v-if="data.publicationDois.length > 0"
            >
              <v-subheader>
                Publications
              </v-subheader>
              <v-divider />
              <v-list
                class="
              transparent"
              >
                <template v-for="(pub, pubIndex) in data.publicationDois">
                  <v-list-item :key="pubIndex">
                    <v-list-item-content v-text="pub" />
                    <v-list-item-action>
                      <v-tooltip top>
                        <template #activator="{ on }">
                          <v-btn
                            icon
                            v-on="on"
                            @click="openLink(`https://doi.org/${item.publication_dois[pubIndex].id}`)"
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
            </template>
            <template v-if="item.dataset_dois.length > 0">
              <v-subheader>
                Data DOIs
              </v-subheader>
              <v-list
                class="transparent"
              >
                <v-divider />
                <v-list-item
                  v-for="(dataDOI, index) in data.datasetDois"
                  :key="index"
                >
                  <v-list-item-content>
                    {{ dataDOI }}
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-tooltip top>
                      <template #activator="{ on }">
                        <v-btn
                          icon
                          v-on="on"
                          @click="openLink(`https://doi.org/${item.dataset_dois[index].id}`)"
                        >
                          <v-icon>mdi-open-in-new</v-icon>
                        </v-btn>
                      </template>
                      <span>Visit site</span>
                    </v-tooltip>
                  </v-list-item-action>
                </v-list-item>
              </v-list>
            </template>
          </div>
        </v-col>
      </v-row>
    </v-main>
  </v-container>
</template>
