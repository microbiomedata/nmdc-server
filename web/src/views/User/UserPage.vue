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
        text: 'ORCID',
        align: 'start',
        sortable: false,
        value: 'orcid',
      },
      { text: 'Name', value: 'name', sortable: false },
      { text: 'Admin', value: 'is_admin', sortable: false },
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

    async function updateAdminStatus(item: User) {
      await api.updateUser(item.id, item);
    }

    return {
      headers,
      users,
      updateAdminStatus,
      options,
      currentUser,
      searchFilter,
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
          outlined
          hide-details
        />
        <v-card outlined>
          <v-data-table
            dense
            :headers="headers"
            :items="users.data.results.results"
            :server-items-length="users.data.results.count"
            :options.sync="options"
            :loading="users.loading.value"
            :items-per-page.sync="users.data.limit"
            :footer-props="{itemsPerPageOptions : [10, 20, 50] }"
            item-key="name"
            class="elevation-1"
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
                class="mt-2"
                :disabled="item.name==currentUser"
                @click="updateAdminStatus(item)"
              />
            </template>
          </v-data-table>
        </v-card>
      </v-card>
    </v-container>
  </v-main>
</template>
