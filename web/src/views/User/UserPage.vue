<script lang="ts">
import { defineComponent, Ref, ref } from '@vue/composition-api';
import { DataTableHeader } from 'vuetify';
import { api, User } from '@/data/api';

export default defineComponent({

  setup() {
    const users: Ref<User[]> = ref([]);

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

    async function populateList() {
      users.value = await api.getAllUsers();
    }

    async function updateAdminStatus(item: User) {
      await api.updateUser(item.id, item);
    }
    populateList();

    return {
      headers,
      populateList,
      users,
      updateAdminStatus,
    };
  },
});
</script>

<template>
  <v-main>
    <v-container>
      <v-card flat>
        <v-card-title class="text-h4">
          Users
        </v-card-title>
        <v-card outlined>
          <v-data-table
            dense
            :headers="headers"
            :items="users"
            item-key="name"
            class="elevation-1"
          >
            <template #[`item.orcid`]="{ item }">
              <a
                :href="`https://orcid.org/${item.orcid}`"
                rel="noopener noreferrer"
                target="_blank"
              >
                {{ item.orcid }}
              </a>
            </template>
            <template #[`item.is_admin`]="{ item }">
              <v-switch
                v-model="item.is_admin"
                class="mt-2"
                @click="updateAdminStatus(item)"
              />
            </template>
          </v-data-table>
        </v-card>
      </v-card>
    </v-container>
  </v-main>
</template>
