<script>
import moment from 'moment';
import Vue from 'vue';
import { groupBy } from 'lodash';
import { opMap } from '@/data/api';
import { fieldDisplayName } from '@/util';

export default Vue.extend({
  props: {
    conditions: {
      type: Array,
      required: true,
    },
    dbSummary: {
      type: Object,
      required: true,
    },
  },

  data: () => ({ menuState: {} }),

  computed: {
    conditionGroups() {
      return Object.entries(groupBy(
        this.conditions,
        (c) => JSON.stringify(({ field: c.field, table: c.table })),
      )).map(([group, conditions]) => {
        const parsed = JSON.parse(group);
        return {
          key: parsed.field + parsed.table,
          field: parsed.field,
          table: parsed.table,
          conditions,
        };
      }).sort((a, b) => a.key.localeCompare(b));
    },
  },

  methods: {
    fieldDisplayName,
    verb(op) {
      return opMap[op];
    },
    valueTransform(val, field, type) {
      // If it's not primitive
      if (val && typeof val === 'object') {
        const inner = val.map((v) => this.valueTransform(v, field, type)).join(', ');
        return `(${inner})`;
      }
      const summary = ((this.dbSummary[type] || {}).attributes || {})[field];
      if (summary) {
        if (['float', 'integer', 'string', 'kegg_search'].includes(summary.type)) {
          return fieldDisplayName(val);
        }
        if (['date'].includes(summary.type)) {
          return moment(val).format('MM/DD/YYYY');
        }
        if (['tree', 'sankey-tree'].includes(summary.type)) {
          return val;
        }
        throw new Error(`Unknown entity type for ${type}: ${field}: ${summary.type}`);
      }
      return val;
    },
    toggleMenu(category, value) {
      Vue.set(this.menuState, category, value);
    },
  },
});
</script>

<template>
  <div>
    <transition-group name="list">
      <v-card
        v-for="group in conditionGroups"
        :key="group.key"
        class="d-flex flex-row pa-1 my-2"
        color="rgb(79, 59, 128, 0.2)"
      >
        <div style="width: 94%">
          <span class="text-subtitle-2">
            {{ fieldDisplayName(group.field, group.table) }}
          </span>
          <span class="text-caption">
            [{{ verb(group.conditions[0].op) }}]
          </span>
          <transition-group name="chip">
            <v-chip
              v-for="cond in group.conditions"
              :key="JSON.stringify(cond.value)"
              small
              close
              label
              class="ma-1 chip"
              style="max-width: 90%;"
              @click:close="$emit('remove', cond)"
            >
              <span class="chip-content">
                {{ valueTransform(cond.value, cond.field, cond.table) }}
              </span>
            </v-chip>
          </transition-group>
        </div>
        <v-menu
          offset-x
          :nudge-right="10"
          :close-on-content-click="false"
          :value="menuState[group.key]"
          @input="toggleMenu(group.key, $event)"
        >
          <template #activator="{ on }">
            <div
              class="expand d-flex flex-column justify-center"
              style="width: 6%"
              v-on="on"
            >
              <v-icon small>
                mdi-play
              </v-icon>
            </div>
          </template>
          <v-card
            width="500"
          >
            <slot
              name="menu"
              v-bind="{
                field: group.field,
                table: group.table,
                isOpen: menuState[group.key],
                toggleMenu: (val) => toggleMenu(group.key, false),
              }"
            />
          </v-card>
        </v-menu>
      </v-card>
    </transition-group>
  </div>
</template>

<style scoped>
.expand {
  border-left: 1px solid grey;
  border-radius: 0 !important;
  cursor: pointer;
}
.chip {
  border: 2px solid;
}
.chip-content {
  overflow: hidden;
}

/* Transition styles for list */
.list-enter-active, .list-leave-active {
  transition: all 0.2s;
}
.list-leave-active {
  position: absolute;
}
.list-enter {
  opacity: 0;
  transform: translateX(100px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(-100px);
}
.list-move {
  transition: transform 0.2s;
}

/* Transition styles for chip */
.chip-enter-active  {
  transition: all 0.2s;
}
.chip-leave-active {
  position: absolute;
}
.chip-enter {
  opacity: 0;
  transform: translateX(100px);
}
.chip-leave-to {
  opacity: 0;
  transform: translateX(-50px);
}
.chip-move {
  transition: transform 0.2s;
}
</style>
