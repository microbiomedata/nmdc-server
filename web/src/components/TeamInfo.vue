<script lang="ts">
import { computed, defineComponent, PropType } from 'vue';
import { StudySearchResults } from '@/data/api';
import OrcidId from '@/components/Presentation/OrcidId.vue';

function getOrcid(person: any) {
  const orcid = person?.applies_to_person?.orcid ?? person?.orcid ?? '';
  return orcid.replace('orcid:', '');
}

const PRINCIPAL_INVESTIGATOR_ROLE = 'Principal Investigator';

export interface TeamMember {
  name: string;
  orcid: string;
  roles: string[];
  image_url?: string;
}

function compareRoles(a: string, b: string) {
  // Sort certain roles first in a predefined order. Others are sorted alphabetically after.
  const roleOrder = [PRINCIPAL_INVESTIGATOR_ROLE];
  const indexA = roleOrder.indexOf(a);
  const indexB = roleOrder.indexOf(b);
  if (indexA !== -1 && indexB !== -1) {
    return indexA - indexB;
  }
  if (indexA !== -1) {
    return -1;
  }
  if (indexB !== -1) {
    return 1;
  }
  return a.localeCompare(b);
}

function compareTeamMembers(a: TeamMember, b: TeamMember) {
  // Sort PIs first, then those with images, then alphabetically by name
  const aIsPI = a.roles.includes(PRINCIPAL_INVESTIGATOR_ROLE) ? 0 : 1;
  const bIsPI = b.roles.includes(PRINCIPAL_INVESTIGATOR_ROLE) ? 0 : 1;
  if (aIsPI !== bIsPI) {
    return aIsPI - bIsPI;
  }

  const aHasImage = a.image_url ? 0 : 1;
  const bHasImage = b.image_url ? 0 : 1;
  if (aHasImage !== bHasImage) {
    return aHasImage - bHasImage;
  }

  return a.name.localeCompare(b.name);
}

export default defineComponent({
  components: { OrcidId },
  props: {
    item: {
      type: Object as PropType<StudySearchResults>,
      required: true,
    },
  },
  setup(props) {
    const team = computed<TeamMember[]>(() => {
      const team: TeamMember[] = (props.item.has_credit_associations || []).map((a) => ({
        name: a.applies_to_person.name || '',
        orcid: getOrcid(a),
        roles: a.applied_roles.sort(compareRoles),
      }));
      const pi_member = team.find((m) => m.orcid === getOrcid(props.item.principal_investigator));
      if (pi_member) {
        // If the PI is already in the team, ensure they have the PI role and image
        if (!pi_member.roles.includes(PRINCIPAL_INVESTIGATOR_ROLE)) {
          pi_member.roles.unshift(PRINCIPAL_INVESTIGATOR_ROLE);
        }
        if (!pi_member.image_url) {
          pi_member.image_url = props.item.principal_investigator_image_url;
        }
      } else {
        // If the PI is not in the team, add them
        team.push({
          name: props.item.principal_investigator.name || '',
          orcid: getOrcid(props.item.principal_investigator),
          roles: [PRINCIPAL_INVESTIGATOR_ROLE],
          image_url: props.item.principal_investigator_image_url,
        });
      }

      // Sort team members
      team.sort(compareTeamMembers);

      return team;
    });

    return {
      team,
    };
  },
});
</script>

<template>
  <v-row>
    <template
      v-for="person in team"
      :key="person.orcid || person.name"
    >
      <v-col
        cols="12"
        md="4"
        class="d-flex"
      >
        <v-avatar
          v-if="person.image_url"
          size="64"
          class="mr-2"
        >
          <v-img
            :src="person.image_url"
            :alt="person.name"
          />
        </v-avatar>

        <div>
          <div class="font-weight-medium">
            <OrcidId
              v-if="person.orcid"
              :orcid-id="person.orcid"
              :name="person.name"
              :authenticated="false"
              :is-name-linked="false"
            />
            <div v-else>
              {{ person.name }}
            </div>
          </div>
          <div class="text-caption">
            {{ person.roles.join(', ') }}
          </div>
        </div>
      </v-col>
    </template>
  </v-row>
</template>
