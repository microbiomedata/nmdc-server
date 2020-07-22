<template>
  <v-container fluid>
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
            <v-list-item-content v-text="doiCitation" />
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
        <v-subheader v-if="publications.length > 0">
          Other publications
        </v-subheader>
        <v-list class="transparent">
          <template
            v-for="(pub, pubIndex) in publications"
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
  </v-container>
</template>
<script>
import { isObject } from 'lodash';
import Cite from 'citation-js';
import {
  typeWithCardinality, valueCardinality, fieldDisplayName,
} from '@/util';

export default {
  props: {
    item: {
      type: Object,
      default: () => {},
    },
  },
  data: () => ({
    doiCitation: '',
    publications: [],
  }),
  computed: {
    displayFields() {
      return Object.keys(this.item).filter((field) => {
        const value = this.item[field];
        if (['name', 'description'].includes(field)) {
          return false;
        }
        return !isObject(value);
      });
    },
  },
  watch: {
    item: {
      async handler() {
        this.doiCitation = null;
        this.publications = [];
        const citationPromises = this.item.publication_dois.map(Cite.async);
        [this.doiCitation, ...this.publications] = (await Promise.all(citationPromises))
          .map((c) => this.formatAPA(c));
      },
      immediate: true,
    },
  },
  methods: {
    fieldDisplayName,
    typeWithCardinality,
    selectField(field) {
      this.$emit('selected', {
        type: 'study',
        conditions: [{
          field, op: '==', value: this.item[field], table: 'study',
        }],
      });
    },
    relatedTypeDescription(relatedType) {
      const n = valueCardinality(this.item[`${relatedType}_id`]);
      return `${n} ${typeWithCardinality(relatedType, n)}`;
    },
    openLink(url) {
      window.open(url, '_blank');
    },
    formatAPA(citation) {
      return citation.format('bibliography', {
        format: 'text',
        template: 'apa',
        lang: 'en-US',
      });
    },
  },
};
</script>
