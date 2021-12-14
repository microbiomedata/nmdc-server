<script lang="ts">
import { computed, defineComponent, PropType } from '@vue/composition-api';
import { StudySearchResults } from '@/data/api';

function getOrcid(person: any) {
  const orcid = person?.applies_to_person?.orcid || '';
  return `https://orcid.org/${orcid.replace('orcid:', '')}`;
}

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<StudySearchResults>,
      required: true,
    },
  },
  setup(props) {
    const team = computed(() => props.item.has_credit_associations
      .filter((m) => m.applies_to_person.name !== props.item.principal_investigator_name));
    const pi = computed(() => props.item.has_credit_associations
      .find((m) => m.applies_to_person.name === props.item.principal_investigator_name));
    const piOrcid = computed(() => getOrcid(pi.value));
    return {
      pi, piOrcid, team, getOrcid,
    };
  },
});
</script>

<template>
  <v-row class="my-6">
    <v-col
      class="shrink"
      offset="1"
    >
      <v-avatar :size="200">
        <v-img :src="item.principal_investigator_image_url" />
      </v-avatar>
    </v-col>
    <v-col class="grow mx-2">
      <v-row
        align="center"
        justify="start"
        style="height: 100%"
      >
        <v-card flat>
          <div class="text-h3">
            {{ pi.applies_to_person.name }}
          </div>
          <div class="text-h5 py-2">
            Principal investigator
          </div>
          <a
            v-for="site in [piOrcid].concat(item.principal_investigator_websites)"
            :key="site"
            class="blue--text py-1"
            style="cursor: pointer; text-decoration: none; display: block;"
            :href="site"
          >
            <v-icon
              left
              color="blue"
            >
              mdi-link
            </v-icon>
            {{ site }}
          </a>
          <div class="text-h5 py-2 primary--text">
            Team
          </div>
          <v-menu
            v-for="member in team"
            :key="member.applies_to_person.orcid"
            bottom
            nudge-bottom="34"
          >
            <template #activator="{ on, attrs }">
              <div
                class="text-subtitle-1 px-1 grey--text text--darken-2"
                style="display: inline-block; text-decoration: underline;"
                v-bind="attrs"
                v-on="on"
              >
                {{ member.applies_to_person.name }}
              </div>
            </template>
            <v-card
              class="pa-2"
            >
              <v-card-title>{{ member.applies_to_person.name }}</v-card-title>
              <v-btn
                text
                color="green"
                :href="getOrcid(member)"
              >
                <img
                  width="24px"
                  class="mr-2"
                  :alt="`${member.applies_to_person.name} profile picture`"
                  src="https://orcid.org/assets/vectors/orcid.logo.icon.svg"
                >
                OrcID
              </v-btn>
            </v-card>
          </v-menu>
        </v-card>
      </v-row>
    </v-col>
  </v-row>
</template>
