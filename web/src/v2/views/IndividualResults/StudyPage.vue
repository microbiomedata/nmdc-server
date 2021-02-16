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

import AttributeList from '@/views/IndividualResults/AttributeList.vue';

export default defineComponent({
  props: {
    id: {
      type: String,
      required: true,
    },
  },

  components: {
    AttributeList,
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

    watch(item, async (_item) => {
      if (_item) {
        data.doiCitation = null;
        data.publications = [];
        const citationPromises = [
          Cite.async(_item.doi),
          ..._item.publication_dois.map(Cite.async),
        ];
        [data.doiCitation, ...data.publications] = (await Promise.all(citationPromises))
          .map((c) => formatAPA(c));
      }
    });

    return {
      data,
      item,
      displayFields,
      /* Methods */
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
        <v-col
          class="flex-grow-1"
        >
          <v-container fluid>
            <v-row>
              <v-col
                class="flex-grow-0"
              >
                <v-avatar :size="200">
                  <v-img
                    :src="item.principal_investigator_image_url"
                  />
                </v-avatar>
              </v-col>
              <v-col
                class="flex-grow-1"
              >
                <v-row
                  align="center"
                  justify="start"
                  style="height: 100%"
                >
                  <v-card flat>
                    <div class="headline">
                      {{ item.principal_investigator_name }}
                    </div>
                    <div class="caption">
                      Principal investigator
                    </div>
                    <div
                      v-for="site in item.principal_investigator_websites"
                      :key="site"
                      class="caption primary--text"
                      style="cursor: pointer"
                      @click="openLink(site)"
                    >
                      <v-icon
                        small
                        left
                        color="primary"
                      >
                        mdi-link
                      </v-icon>
                      {{ site }}
                    </div>
                  </v-card>
                </v-row>
              </v-col>
            </v-row>
          </v-container>
          <div class="headline">
            {{ item.name }}
          </div>
          <div class="mt-3">
            <span class="font-weight-bold">Scientific objective: </span>
            {{ item.scientific_objective }}
          </div>
        </v-col>
        <v-col class="flex-grow-1 grey lighten-4 px-0 pb-0">
          <v-subheader>Citation</v-subheader>
          <v-list class="transparent">
            <v-divider />
            <v-list-item>
              <v-list-item-content v-text="data.doiCitation" />
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
            <template
              v-for="(pub, pubIndex) in data.publications"
            >
              <v-divider :key="`${pubIndex}-divider`" />
              <v-list-item
                :key="pubIndex"
              >
                <v-list-item-content
                  v-text="pub"
                />
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
        </v-col>
      </v-row>
      <AttributeList
        :item="item"
        type="study"
      />
    </v-main>
  </v-container>
</template>
