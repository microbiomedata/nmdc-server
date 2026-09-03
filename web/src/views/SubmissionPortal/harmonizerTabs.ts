import {
  HARMONIZER_TEMPLATES,
  HarmonizerTemplateInfo,
  TemplateName,
} from './types';

type HarmonizerDataBySlot = Record<string, any[]>;

/**
 * Derive the active Data Harmonizer template from the selected Vuetify tab index.
 */
export function getHarmonizerTemplateForTab(
  templateList: readonly TemplateName[],
  activeTabIndex: number,
): { key: TemplateName | null, template: HarmonizerTemplateInfo | null } {
  const key = templateList[activeTabIndex] ?? null;
  return {
    key,
    template: key === null ? null : HARMONIZER_TEMPLATES[key],
  };
}

/**
 * Get the saved sample metadata rows for a template's sample data slot.
 */
export function getHarmonizerTemplateData(
  data: HarmonizerDataBySlot,
  template: HarmonizerTemplateInfo | null,
) {
  if (!template?.sampleDataSlot) {
    return [];
  }
  return data[template.sampleDataSlot] || [];
}
