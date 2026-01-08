<script lang="ts">
import {
  defineComponent,
  ref,
  watch,
} from 'vue';
// @ts-ignore
import { fieldDisplayName } from '@/util';
import { downloadJson } from '@/utils';
import {
  api,
  Condition,
  DoiInfo,
  StudySearchResults,
} from '@/data/api';
import { setConditions, setUniqueCondition } from '@/store';
import AppBanner from '@/components/AppBanner.vue';
import IndividualTitle from '@/views/IndividualResults/IndividualTitle.vue';
import ClickToCopyText from '@/components/Presentation/ClickToCopyText.vue';
import TeamInfo from '@/components/TeamInfo.vue';
import RevealContainer from '@/components/Presentation/RevealContainer.vue';
import usePaginatedResults from '@/use/usePaginatedResults';
import BiosampleSearchResults from '@/components/Presentation/BiosampleSearchResults.vue';
import { urlify } from '@/data/utils';
import useRequest from '@/use/useRequest';
import PageSection from '@/views/IndividualResults/PageSection.vue';
import AttributeRow from '@/components/Presentation/AttributeRow.vue';
import DoiCitation from '@/components/Presentation/DoiCitation.vue';
import DownloadDialog from '@/components/DownloadDialog.vue';
import ErrorDialog from '@/components/ErrorDialog.vue';

const GOLD_STUDY_LINK_BASE = 'https://gold.jgi.doe.gov/study?id=';
const BIOPROJECT_LINK_BASE = 'https://bioregistry.io/';
const DEFAULT_BIOSAMPLE_PAGE_SIZE = 5;

export default defineComponent({
  components: {
    AppBanner,
    AttributeRow,
    BiosampleSearchResults,
    ClickToCopyText,
    DoiCitation,
    DownloadDialog,
    ErrorDialog,
    IndividualTitle,
    PageSection,
    RevealContainer,
    TeamInfo,
  },

  props: {
    id: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const study = ref<StudySearchResults | null>(null);
    const studyDownloadDialog = ref(false);
    const studyDownloadLoading = ref(false);
    const errorDialog = ref(false);
    const sampleCount = ref(0);
    const omicsProcessingCounts = ref<Record<string, number> | null>(null);

    const parentStudies = ref<StudySearchResults[]>([]);
    const conditions = ref<Condition[]>([]);
    const biosampleSearchEnabled = ref(false);

    const publicationDois = ref<DoiInfo[]>([]);
    const awardDois = ref<DoiInfo[]>([]);
    const datasetDois = ref<DoiInfo[]>([]);

    const goldLinks = ref<string[]>([]);
    const bioprojectLinks = ref<string[]>([]);
    const websiteLinks = ref<string[]>([]);

    const biosampleSearch = usePaginatedResults(
      conditions,
      api.searchBiosample,
      undefined,
      DEFAULT_BIOSAMPLE_PAGE_SIZE,
      biosampleSearchEnabled,
    );

    const getStudyRequest = useRequest();

    async function downloadStudyMetadata() {
      try {
        studyDownloadDialog.value = false;
        studyDownloadLoading.value = true;
        const data = await api.getStudySource(props.id);
        downloadJson(data, `${props.id}.json`);
      } catch (error) {
        console.error('Failed to download study metadata:', error);
        errorDialog.value = true;
      } finally {
        studyDownloadLoading.value = false;
      }
    }

    watch(() => props.id, () => getStudyRequest.request(async () => {
      biosampleSearch.reset();

      const _study = await api.getStudy(props.id);

      sampleCount.value = _study.children.reduce((prev, curr) => prev + curr.sample_count, _study.sample_count);
      omicsProcessingCounts.value = null;
      if (_study.omics_processing_counts !== null) {
        const counts: Record<string, number> = {};
        _study.omics_processing_counts.forEach(({type, count}) => {
          if (type.toLowerCase() !== 'lipidomics' && count > 0) {
            counts[type] = count;
          }
        });
        omicsProcessingCounts.value = counts;
      }

      if (_study.part_of) {
        parentStudies.value = await Promise.all(
          _study.part_of.map((id) => api.getStudy(id)),
        );
      } else {
        parentStudies.value = [];
      }

      publicationDois.value = Object.values(_study.doi_map).filter((doi) => doi.category === 'publication_doi');
      awardDois.value = Object.values(_study.doi_map).filter((doi) => doi.category === 'award_doi');
      datasetDois.value = Object.values(_study.doi_map).filter((doi) => doi.category === 'dataset_doi');

      goldLinks.value = (_study.gold_study_identifiers || []).map((gold_id: string) => (
        GOLD_STUDY_LINK_BASE + gold_id.replace('gold:', '')
      ));
      bioprojectLinks.value = (_study.annotations?.insdc_bioproject_identifiers || []).map((id: string) => (
        BIOPROJECT_LINK_BASE + id
      ));
      websiteLinks.value = [
        ...(_study.homepage_website || []),
        ...(_study.principal_investigator_websites || []),
      ];

      conditions.value = [{
        op: '==',
        table: 'study',
        field: 'study_id',
        value: _study.id,
      }];
      if (_study.children.length > 0) {
        _study.children.forEach((child: StudySearchResults) => {
          conditions.value.push({
            value: child.id,
            table: 'study',
            field: 'study_id',
            op: '==',
          });
        });
      }
      biosampleSearchEnabled.value = true;

      study.value = _study;
    }), {
      immediate: true,
    });

    function seeStudyInContext() {
      setConditions(conditions.value, true);
    }

    function seeOmicsForStudy(omicsType = '') {
      setUniqueCondition(
        ['study_id', 'omics_type'],
        ['study', 'omics_processing'],
        [
          {
            value: props.id,
            table: 'study',
            op: '==',
            field: 'id',
          },
          {
            value: omicsType,
            table: 'omics_processing',
            field: 'omics_type',
            op: '==',
          },
        ],
        true,
      );
    }

    return {
      study,
      sampleCount,
      omicsProcessingCounts,
      loading: getStudyRequest.loading,
      goldLinks,
      bioprojectLinks,
      websiteLinks,
      publicationDois,
      awardDois,
      datasetDois,
      biosampleSearch,
      parentStudies,
      /* Methods */
      fieldDisplayName,
      seeStudyInContext,
      seeOmicsForStudy,
      urlify,
      downloadStudyMetadata,
      studyDownloadDialog,
      studyDownloadLoading,
      errorDialog,
    };
  },
});
</script>

<template>
  <v-main>
    <AppBanner />
    <v-container v-if="loading">
      <v-skeleton-loader type="article" />
    </v-container>
    <v-container v-if="!loading && study !== null">
      <div class="text-caption">
        <!-- eslint-disable-next-line-->
        <router-link :to="{ name: 'Search' }">Home</router-link>
        <span class="mx-2">/</span>
        <ClickToCopyText>{{ study.id }}</ClickToCopyText>
      </div>

      <PageSection>
        <v-row class="mt-0">
          <v-col
            cols="12"
            :md="study.image_url ? 8 : 12"
          >
            <IndividualTitle :item="study">
              <template
                v-if="study.description"
                #subtitle
              >
                <RevealContainer>
                  <span v-html="urlify(study.description)" />
                </RevealContainer>
              </template>
            </IndividualTitle>
            <v-dialog
              v-model="studyDownloadDialog"
              max-width="400"
            >
              <template #activator="{ props }">
                <v-btn
                  v-bind="props"
                  class="mt-2 mb-8"
                  color="primary"
                  size="small"
                >
                  <v-icon class="mr-2">
                    mdi-download
                  </v-icon>
                  Download Study Metadata
                </v-btn>
              </template>
              <DownloadDialog
                :loading="studyDownloadLoading"
                @clicked="downloadStudyMetadata"
              />
            </v-dialog>
            <v-snackbar
              v-model="studyDownloadLoading"
              location="right bottom"
              timeout="-1"
            >
              <v-progress-circular
                indeterminate
                class="mr-3"
              />
              <span>
                Downloading study metadata
              </span>
            </v-snackbar>
            <ErrorDialog
              v-model:show="errorDialog"
            />
            <AttributeRow
              v-if="parentStudies.length > 0"
              label="Part Of"
            >
              <div class="stack-sm">
                <div
                  v-for="parent in parentStudies"
                  :key="parent.id"
                >
                  <router-link
                    :to="{ name: 'Study', params: { id: parent.id }}"
                  >
                    {{ parent.annotations.title }}
                  </router-link>
                </div>
              </div>
            </AttributeRow>

            <AttributeRow
              v-if="study.children.length > 0"
              label="Associated Studies"
            >
              <div class="stack-sm">
                <div
                  v-for="child in study.children"
                  :key="child.id"
                >
                  <router-link
                    :to="{ name: 'Study', params: { id: child.id }}"
                  >
                    {{ child.annotations.title }}
                  </router-link>
                </div>
              </div>
            </AttributeRow>

            <AttributeRow
              v-if="sampleCount > 0 || omicsProcessingCounts !== null"
              label="Data Summary"
            >
              <v-chip
                v-if="sampleCount > 0"
                class="mb-4"
                size="small"
                color="primary"
                variant="flat"
                @click="seeStudyInContext"
              >
                All Samples: {{ sampleCount }}
              </v-chip>
              <div v-if="omicsProcessingCounts !== null">
                <div class="text-caption font-weight-medium">
                  Omics Types
                </div>
                <template
                  v-for="(count, type) in omicsProcessingCounts"
                  :key="type"
                >
                  <v-chip
                    class="mr-2"
                    size="small"
                    @click="seeOmicsForStudy(type)"
                  >
                    {{ fieldDisplayName(type) }}: {{ count }}
                  </v-chip>
                </template>
              </div>
            </AttributeRow>
          </v-col>

          <v-col
            v-if="study.image_url"
            cols="12"
            md="4"
          >
            <v-img
              :src="study.image_url"
              :alt="study.name"
              contain
              max-width="450"
            />
          </v-col>
        </v-row>
      </PageSection>

      <PageSection heading="Team">
        <RevealContainer :closed-height="150">
          <TeamInfo :item="study" />
        </RevealContainer>
      </PageSection>

      <PageSection heading="Study Details">
        <AttributeRow
          v-if="publicationDois.length > 0"
          label="Publications"
        >
          <div class="stack-sm">
            <DoiCitation
              v-for="doi in publicationDois"
              :key="doi.info.DOI"
              :doi="doi"
            />
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="study.funding_sources && study.funding_sources.length > 0"
          label="Funding Sources"
        >
          <div class="stack-sm">
            <span
              v-for="source in study.funding_sources"
              :key="source"
              v-html="urlify(source)"
            />
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="awardDois.length > 0"
          label="Awards"
        >
          <div class="stack-sm">
            <DoiCitation
              v-for="doi in awardDois"
              :key="doi.info.DOI"
              :doi="doi"
            />
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="websiteLinks.length > 0"
          label="Websites"
        >
          <div class="stack-sm">
            <div
              v-for="url in websiteLinks"
              :key="url"
            >
              <a
                :href="url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ url }}
              </a>
            </div>
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="study.protocol_link && study.protocol_link.length > 0"
          label="Protocols"
        >
          <div class="stack-sm">
            <div
              v-for="link in study.protocol_link"
              :key="link"
            >
              <a
                :href="link"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ link }}
              </a>
            </div>
          </div>
        </AttributeRow>
      </PageSection>

      <PageSection heading="Related External Resources">
        <AttributeRow
          v-if="datasetDois.length > 0"
          label="Datasets"
        >
          <div class="stack-sm">
            <DoiCitation
              v-for="doi in datasetDois"
              :key="doi.info.DOI"
              :doi="doi"
            />
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="goldLinks.length > 0"
          label="GOLD Studies"
        >
          <div class="stack-sm">
            <div
              v-for="link in goldLinks"
              :key="link"
            >
              <a
                :href="link"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ link }}
              </a>
            </div>
          </div>
        </AttributeRow>

        <AttributeRow
          v-if="bioprojectLinks.length > 0"
          label="BioProjects"
        >
          <div class="stack-sm">
            <div
              v-for="link in bioprojectLinks"
              :key="link"
            >
              <a
                :href="link"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ link }}
              </a>
            </div>
          </div>
        </AttributeRow>
      </PageSection>

      <PageSection heading="Samples">
        <v-skeleton-loader
          v-if="biosampleSearch.fetchCount.value === 0"
          type="list-item-three-line, list-item-three-line"
        />

        <div v-if="biosampleSearch.data.results.count > 0">
          <BiosampleSearchResults
            :biosample-search="biosampleSearch"
            :data-object-filter="[]"
          />
        </div>
      </PageSection>
    </v-container>
  </v-main>
</template>
