<script lang="ts">
import {
  computed, defineComponent, watchEffect, ref, watch,
} from '@vue/composition-api';

import { isObject } from 'lodash';
// @ts-ignore
import Cite from 'citation-js';
import {
  typeWithCardinality, valueCardinality, fieldDisplayName,
} from '@/util';
import {
  api, StudySearchResults, DOI, Condition,
} from '@/data/api';
import { setUniqueCondition, setConditions } from '@/store';
import { useRouter } from '@/use/useRouter';
import AppBanner from '@/components/AppBanner.vue';
import AttributeItem from '@/components/Presentation/AttributeItem.vue';
import IndividualTitle from '@/views/IndividualResults/IndividualTitle.vue';
import TeamInfo from '@/components/TeamInfo.vue';
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
    AppBanner,
    AttributeItem,
    IndividualTitle,
    TeamInfo,
  },

  props: {
    id: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const dois = ref({
      awardDois: [] as DOI[],
      publicationDois: [] as DOI[],
      datasetDois: [] as DOI[],
      massiveDois: [] as DOI[],
      essDiveDois: [] as DOI[],
    });

    const item = ref(null as StudySearchResults | null);
    const parentStudies = ref([]as StudySearchResults[]);

    watch(item, () => {
      if (item.value?.part_of) {
        item.value.part_of.forEach((id: string) => {
          if (!parentStudies.value.some((study) => study.id === id)) {
            api.getStudy(id).then((b) => {
              parentStudies.value.push(b);
            });
          }
        });
      } else {
        parentStudies.value = [];
      }
    });

    watchEffect(() => {
      api.getStudy(props.id).then((b) => { item.value = b; });
    });

    const studyData = computed(() => Object.values(item)
      .map((val) => ({
        ...val,
        sample_count: val?.children?.reduce((acc: number, child: StudySearchResults) => acc + child.sample_count, val.sample_count),
      }))[0]);

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
      if (!item.value?.gold_study_identifiers && !item.value?.open_in_gold) {
        return new Set();
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
      router.go({ name: 'Search' });
    }

    function seeStudyInContext(item: StudySearchResults) {
      const conditions: Condition[] = [{
        op: '==',
        table: 'study',
        field: 'study_id',
        value: props.id,
      }];
      if (item.children.length > 0) {
        item.children.forEach((child: StudySearchResults) => {
          conditions.push({
            value: child.id,
            table: 'study',
            field: 'study_id',
            op: '==',
          });
        });
      }
      setConditions(conditions, true);
    }

    watch(item, async (_item) => {
      const doiMap = _item?.doi_map;
      if (doiMap) {
        dois.value.awardDois = [];
        dois.value.publicationDois = [];
        dois.value.datasetDois = [];
        dois.value.awardDois = Object.values(doiMap)
          .filter((doi) => doi.category === 'award_doi')
          .map((doi) => [{
            cite: CitationOverrides[doi.info.DOI] || formatAPA(new Cite(doi.info.DOI)),
            id: doi.info.DOI,
            provider: doi.provider,
          }]).flat();
        dois.value.datasetDois = Object.values(doiMap)
          .filter((doi) => doi.category === 'dataset_doi')
          .map((doi) => [{
            cite: CitationOverrides[doi.info.DOI] || formatAPA(new Cite(doi.info.DOI)),
            id: doi.info.DOI,
            provider: doi.provider,
          }]).flat();
        dois.value.publicationDois = Object.values(doiMap)
          .filter((doi) => doi.category === 'publication_doi')
          .map((doi) => [{
            cite: CitationOverrides[doi.info.DOI] || formatAPA(new Cite(doi.info.DOI)),
            id: doi.info.DOI,
            provider: doi.provider,
          }]).flat();
      }
    });
    return {
      CitationOverrides,
      GoldStudyLinkBase,
      goldLinks,
      data: dois,
      item,
      studyData,
      displayFields,
      /* Methods */
      seeOmicsForStudy,
      relatedTypeDescription,
      openLink,
      formatAPA,
      typeWithCardinality,
      fieldDisplayName,
      seeStudyInContext,
      parentStudies,
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
      <AppBanner />
      <v-row :class="{'flex-column': $vuetify.breakpoint.xs}">
        <v-col
          cols="12"
          md="7"
        >
          <v-container>
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
              </template>
            </IndividualTitle>
            <TeamInfo
              :item="item"
            />
          </v-container>
          <v-col offset="1">
            <div class="display-1">
              NMDC Details
            </div>
            <v-list>
              <AttributeItem
                v-bind="{ item, field: 'id', bindClick: true }"
                @click="seeStudyInContext(item)"
              />
              <AttributeItem
                v-bind="{ item: studyData, field: 'sample_count', bindClick: true }"
                @click="seeStudyInContext(item)"
              />
            </v-list>
            <template
              v-if="
                goldLinks.size > 0 ||
                  item.relevant_protocols||
                  item.principal_investigator_websites.length > 0"
            >
              <div class="display-1">
                Additional Resources
              </div>
              <v-list
                v-if="goldLinks.size > 0 || item.relevant_protocols.length > 0"
              >
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
                <AttributeItem
                  v-for="proto in (item.relevant_protocols || [])"
                  :key="proto"
                  style="padding-left: 60px;"
                  v-bind="{
                    item,
                    link: { name: proto, target: proto},
                    field: 'relevant_protocols' }
                  "
                />
                <v-list-item v-if="item.principal_investigator_websites.length > 0">
                  <v-list-item-avatar>
                    <v-icon>mdi-file-document</v-icon>
                  </v-list-item-avatar>
                  <v-list-item-content>
                    <v-list-item-title class="text-h6">
                      Links
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
                      name: 'GOLD Metadata',
                      target: link
                    }
                  }"
                  :image="images.gold"
                />
                <template
                  v-for="site in (item.principal_investigator_websites || [])"
                >
                  <AttributeItem
                    :key="site"
                    style="padding-left: 60px;"
                    v-bind="{
                      item,
                      link: { name: site, target: site},
                    }
                    "
                  />
                </template>
              </v-list>
            </template>
          </v-col>
        </v-col>
        <v-col
          cols="12"
          md="5"
        >
          <div
            v-if="Object.keys(item.doi_map).length > 0"
            class="ma-4 pa-2 grey lighten-4"
          >
            <template v-if="data.awardDois.length > 0">
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
                    {{ award.cite }}
                    <div
                      v-if="award.provider"
                      class="pt-2"
                    >
                      <span class="font-weight-bold pr-2">Provider:</span>
                      <span class="text-uppercase">{{ award.provider }}</span>
                    </div>
                  </v-list-item-content>

                  <v-list-item-action>
                    <v-tooltip top>
                      <template #activator="{ on }">
                        <v-btn
                          icon
                          v-on="on"
                          @click="openLink(`https://doi.org/${award.id}`)"
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
                    <v-list-item-content>
                      {{ pub.cite }}
                      <div
                        v-if="pub.provider"
                        class="pt-2"
                      >
                        <span class="font-weight-bold pr-2">Provider:</span>
                        <span class="text-uppercase">{{ pub.provider }}</span>
                      </div>
                    </v-list-item-content>
                    <v-list-item-action>
                      <v-tooltip top>
                        <template #activator="{ on }">
                          <v-btn
                            icon
                            v-on="on"
                            @click="openLink(`https://doi.org/${pub.id}`)"
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
            <template v-if="data.datasetDois.length > 0">
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
                    {{ dataDOI.cite }}
                    <div
                      v-if="dataDOI.provider"
                      class="pt-2"
                    >
                      <span class="font-weight-bold pr-2">Provider:</span>
                      <span class="text-uppercase">{{ dataDOI.provider }}</span>
                    </div>
                  </v-list-item-content>
                  <v-list-item-action>
                    <v-tooltip top>
                      <template #activator="{ on }">
                        <v-btn
                          icon
                          v-on="on"
                          @click="openLink(`https://doi.org/${dataDOI.id}`)"
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
          <v-card
            v-if="item.part_of && item.part_of.length > 0"
            flat
          >
            <v-card-title class="display-1">
              Part of:
            </v-card-title>
            <v-list>
              <v-list-item
                v-for="study in parentStudies"
                :key="study.id"
                :to="`${study.id}`"
              >
                <v-list-item-icon>
                  <v-icon>mdi-file-document</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title class="px-2">
                    {{ study.annotations.title }}
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card>
          <v-card
            v-if="item.children && item.children.length > 0"
            flat
          >
            <v-card-title class="display-1">
              Associated Studies:
            </v-card-title>
            <v-list>
              <v-list-item
                v-for="study in item.children"
                :key="study.id"
                :to="`${study.id}`"
              >
                <v-list-item-icon>
                  <v-icon>mdi-file-document</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title class="px-2">
                    {{ study.annotations.title }}
                  </v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>
      </v-row>
    </v-main>
  </v-container>
</template>
