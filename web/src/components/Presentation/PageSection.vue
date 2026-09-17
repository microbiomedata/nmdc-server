<script setup lang="ts">
/**
 * PageSection is a first-level organization unit for detail pages. It
 * provides an optional heading, descriptive subheading, and a slot for content. If no content is
 * provided, a fallback message is displayed.
 *
 * See also: AttributeRow.vue for a second-level organization unit within
 *    a PageSection.
 */
withDefaults(defineProps<{
  /**
   * Optional heading for the section. If not provided, the 'heading' slot
   * will be used instead. If neither is provided, no heading will be
   * displayed.
   */
  heading?: string;
  subheading?: string;
  helpLink?: string;
  helpTooltip?: string;
}>(), {
  heading: '',
  subheading: '',
  helpLink: undefined,
  helpTooltip: undefined,
});
</script>

<template>
  <div class="mb-16">
    <div class="mb-4">
      <div
        v-if="heading || $slots.heading"
        class="text-h5 d-flex align-center"
      >
        <template v-if="heading">
          {{ heading }}
        </template>
        <template v-else>
          <slot name="heading" />
        </template>
        <v-tooltip
          v-if="helpLink || helpTooltip"
          location="right"
          max-width="340px"
        >
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="plain"
              size="small"
              :href="helpLink"
              target="_blank"
              rel="noopener noreferrer"
            >
              <v-icon>mdi-help-circle</v-icon>
            </v-btn>
          </template>
          <span>
            {{ helpTooltip || 'Click for more information' }}
          </span>
        </v-tooltip>
      </div>
      <div
        v-if="subheading || $slots.subheading"
        class="text-subtitle-1"
      >
        <template v-if="subheading">
          {{ subheading }}
        </template>
        <template v-else>
          <slot name="subheading" />
        </template>
      </div>
    </div>
    <slot>
      <i class="text-medium-emphasis">
        No information available
      </i>
    </slot>
  </div>
</template>
