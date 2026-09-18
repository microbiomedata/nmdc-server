<script setup lang="ts">
import { computed } from 'vue';
import type { PrincipalInvestigator, StudySearchResult } from '@/data/api';
import OrcidId from '@/components/Presentation/OrcidId.vue';

function getOrcid(person: any) {
  const orcid = person?.applies_to_agent?.orcid ?? person?.orcid ?? '';
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

const props = defineProps<{ item: StudySearchResult }>();

function isSamePerson(member: TeamMember, principalInvestigator: PrincipalInvestigator) {
  const orcid = getOrcid(principalInvestigator);
  return orcid ? member.orcid === orcid : member.name === principalInvestigator.name;
}

const team = computed<TeamMember[]>(() => {
  const teamMembers: TeamMember[] = (props.item.has_credit_associations || []).map(
    (association) => ({
      name: association.applies_to_agent.name,
      orcid: getOrcid(association),
      roles: [...association.applied_roles].sort(compareRoles),
    }),
  );

  props.item.principal_investigators.forEach((principalInvestigator) => {
    const isExistingMember = teamMembers.find((member) => isSamePerson(member, principalInvestigator));
    if (isExistingMember) {
      if (!isExistingMember.roles.includes(PRINCIPAL_INVESTIGATOR_ROLE)) {
        isExistingMember.roles.unshift(PRINCIPAL_INVESTIGATOR_ROLE);
      }
      isExistingMember.image_url ||= principalInvestigator.profile_image_url || undefined;
    } else {
      teamMembers.push({
        name: principalInvestigator.name,
        orcid: getOrcid(principalInvestigator),
        roles: [PRINCIPAL_INVESTIGATOR_ROLE],
        image_url: principalInvestigator.profile_image_url || undefined,
      });
    }
  });

  return teamMembers.sort(compareTeamMembers);
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
