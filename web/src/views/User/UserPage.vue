<script lang="ts">
import { defineComponent, ref, watch } from 'vue';
import { DataTableHeader } from 'vuetify';
import { api, SearchParams, SearchResponse } from '@/data/api';
import { stateRefs } from '@/store';
import { User } from '@/types';
import usePaginatedResults from '@/use/usePaginatedResults';
import AppBanner from '@/components/AppBanner.vue';
import OrcidId from '../../components/Presentation/OrcidId.vue';

export default defineComponent({
  components: { AppBanner, OrcidId },

  setup() {
    const currentUser = stateRefs.user;
    const itemsPerPage = 10;
    const options = ref({
      page: 1,
      itemsPerPage,
    });
    const searchFilter = ref('');
    const headers : DataTableHeader[] = [
      {
        title: 'ORCID',
        align: 'start',
        sortable: false,
        value: 'orcid',
      },
      { title: 'Name', value: 'name', sortable: false },
      { title: 'Admin', value: 'is_admin', sortable: false },
    ];

    async function getUsers(params: SearchParams): Promise<SearchResponse<User>> {
      return api.getAllUsers(params, searchFilter.value);
    }

    const users = usePaginatedResults(ref([]), getUsers, ref([]), itemsPerPage);
    watch(options, () => users.setPage(options.value.page), { deep: true });
    watch(searchFilter, () => {
      options.value.page = 1;
      users.setPage(options.value.page);
    }, { deep: true });

    const updating = ref(false);
    async function updateAdminStatus(item: User) {
      updating.value = true;
      try {
        await api.updateUser(item.id, item);
        await users.refetch();
      } finally {
        updating.value = false;
      }
    }

    return {
      headers,
      users,
      updateAdminStatus,
      options,
      currentUser,
      searchFilter,
      updating,
    };
  },
});
</script>

<template>
  <v-main>
    <AppBanner />
    <v-container>
      <v-card flat>
        <v-card-title class="text-h4">
          Users
        </v-card-title>
        <v-text-field
          v-model="searchFilter"
          label="Search Users"
          class="mb-2"
          variant="outlined"
          hide-details
        />
        <v-card variant="outlined">
          <v-data-table-server
            v-model:options="options"
            v-model:items-per-page="users.data.limit"
            density="compact"
            :headers="headers"
            :items="users.data.results.results"
            :items-length="users.data.results.count"
            :items-per-page-options="[10, 20, 50]"
            :loading="users.loading.value || updating"
          >
            <template #[`item.orcid`]="{ item }">
              <orcid-id
                :orcid-id="item.orcid"
                :authenticated="true"
                :width="24"
              />
            </template>
            <template #[`item.is_admin`]="{ item }">
              <v-switch
                v-model="item.is_admin"
                color="primary"
                hide-details
                :disabled="item.name==currentUser?.name"
                @update:model-value="updateAdminStatus(item)"
              />
            </template>
          </v-data-table-server>
        </v-card>
      </v-card>
    </v-container>
  </v-main>
</template>
