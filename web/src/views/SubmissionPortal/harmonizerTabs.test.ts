import { describe, expect, it } from 'vitest';

import {
  getHarmonizerTemplateData,
  getHarmonizerTemplateForTab,
} from './harmonizerTabs';
import { HARMONIZER_TEMPLATES, TemplateName } from './types';

describe('harmonizer tab state', () => {
  it('derives the active template key and metadata from the active tab index', () => {
    const templateList: TemplateName[] = ['soil', 'water'];

    expect(getHarmonizerTemplateForTab(templateList, 1)).toEqual({
      key: 'water',
      template: HARMONIZER_TEMPLATES.water,
    });
  });

  it('returns null template state for an out-of-range active tab index', () => {
    expect(getHarmonizerTemplateForTab(['soil'], 3)).toEqual({
      key: null,
      template: null,
    });
  });

  it('derives active template data from the active template sample slot', () => {
    const template = HARMONIZER_TEMPLATES.soil;
    const soilData = [{ samp_name: 'soil-1' }];

    expect(getHarmonizerTemplateData({
      soil_data: soilData,
      water_data: [{ samp_name: 'water-1' }],
    }, template)).toBe(soilData);
  });

  it('returns an empty array when the active template is missing', () => {
    expect(getHarmonizerTemplateData({}, null)).toEqual([]);
  });
});
