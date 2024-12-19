<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';
import { StudySearchResults } from '@/data/api';
import OrcidId from './Presentation/OrcidId.vue';

function getOrcid(person: any) {
  const orcid = person?.applies_to_person?.orcid ?? person?.orcid ?? '';
  return orcid.replace('orcid:', '');
}

export default defineComponent({
  components: {
    OrcidId,
  },
  props: {
    item: {
      type: Object as PropType<StudySearchResults>,
      required: true,
    },
  },
  setup(props) {
    const team = computed(() => props.item.has_credit_associations);
    const hasOrcid = computed(() => props.item.principal_investigator?.orcid);
    return {
      team, getOrcid, hasOrcid,
    };
  },
});
</script>

<template>
  <!-- Adjust alignment when there isn't an image to display -->
  <v-row
    class="my-6"
    :no-gutters=" !item.image_url && !item.principal_investigator_image_url"
  >
    <v-col
      class="shrink"
      offset="1"
    >
      <v-img
        v-if="item.image_url"
        :key="item.image_url"
        :src="item.image_url"
        width="200"
      />
      <v-avatar
        v-else-if="item.principal_investigator_image_url"
        :size="200"
      >
        <v-img
          :src="item.principal_investigator_image_url"
          :contain="item.id === 'gold:Gs0110119'"
          position="40% 25%"
        />
      </v-avatar>
    </v-col>
    <v-col
      class="grow mx-4 pr-8"
    >
      <v-row
        align="center"
        justify="start"
        style="height: 100%"
      >
        <v-card flat>
          <div v-if="item.study_category != 'consortium' && item.principal_investigator">
            <div class="text-h3">
              {{ item.principal_investigator_name }}
            </div>
            <div class="text-h5 py-2">
              Principal investigator
            </div>
            <span
              v-if="hasOrcid"
              style="display: flex; align-items: center;"
              class="py-1"
            >
              <orcid-id
                :orcid-id="getOrcid(item.principal_investigator)"
                :authenticated="false"
                :width="24"
              />
            </span>
          </div>
          <div
            v-if="item.homepage_website && item.homepage_website[0]"
            class="text-h5 py-2 primary--text"
          >
            Consortium Homepage: <a :href="item.homepage_website">{{ item.homepage_website[0] }}</a>
          </div>
          <div
            v-if="team"
            class="text-h5 py-2 primary--text"
          >
            Team
          </div>
          <div class="team">
            <v-menu
              v-for="member in team"
              :key="member.applies_to_person.orcid"
              bottom
              max-width="450px"
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
                class=" d-flex flex-column justify-start pa-2"
              >
                <v-card-title>{{ member.applies_to_person.name }}</v-card-title>
                <v-card-subtitle>CRediT: {{ member.applied_roles.join(', ') }}</v-card-subtitle>
                <orcid-id
                  v-if="member.applies_to_person.orcid"
                  :orcid-id="getOrcid(member)"
                  :authenticated="false"
                  :width="24"
                />
              </v-card>
            </v-menu>
          </div>
          <div v-if="item.funding_sources">
            <div class="text-h5 py-2 primary--text">
              Funding Sources
            </div>
            <div>
              {{ item.funding_sources.flat().toString() }}
            </div>
          </div>
        </v-card>
      </v-row>
    </v-col>
  </v-row>
</template>

<style>
.team {
-webkit-line-clamp: 3;
display: -webkit-box;
-webkit-box-orient: vertical;
overflow-y: auto;
width: fit-content;
}
</style>
