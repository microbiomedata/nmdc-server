import { ref, Ref } from '@vue/composition-api';

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES = {
  'CanCOGeN Covid-19': { folder: 'canada_covid19', status: 'published' },
  'GISAID (ALPHA)': { folder: 'gisaid', status: 'draft' },
  'MIxS air': { folder: 'air', status: 'published' },
  'MIxS built environment': { folder: 'built_environment', status: 'published' },
  'MIxS host-associated': { folder: 'host_associated', status: 'published' },
  'MIxS human-associated': { folder: 'human_associated', status: 'published' },
  'MIxS human-gut': { folder: 'human_gut', status: 'published' },
  'MIxS human-oral': { folder: 'human_oral', status: 'published' },
  'MIxS human-skin': { folder: 'human_skin', status: 'published' },
  'MIxS human-vaginal': { folder: 'human_vaginal', status: 'published' },
  'MIxS hydrocarbon resources-cores': { folder: 'hydrocarbon_resources_cores', status: 'published' },
  'MIxS hydrocarbon resources-fluids/swabs': { folder: 'hydrocarbon_resources_fluids_swabs', status: 'published' },
  'MIxS microbial mat/biofilm': { folder: 'microbial_mat_biofilm', status: 'published' },
  'MIxS plant-associated': { folder: 'plant_associated', status: 'published' },
  'MIxS sediment': { folder: 'sediment', status: 'published' },
  'MIxS soil': { folder: 'soil', status: 'published' },
  'MIxS wastewater/sludge': { folder: 'wastewater_sludge', status: 'published' },
  'MIxS water': { folder: 'water', status: 'published' },
  'Index of Terms culture_environmental': { folder: 'IoT_culture_environmental', status: 'published' },
  'Index of Terms mixed_culture': { folder: 'IoT_mixed_culture', status: 'published' },
  'Index of Terms plant_associated': { folder: 'IoT_plant_associated', status: 'published' },
  'Index of Terms pore_water': { folder: 'IoT_pore_water', status: 'published' },
  'Index of Terms pure_culture': { folder: 'IoT_pure_culture', status: 'published' },
  'Index of Terms sediment': { folder: 'IoT_sediment', status: 'published' },
  'Index of Terms soil': { folder: 'IoT_soil', status: 'published' },
  'Index of Terms water': { folder: 'IoT_water', status: 'published' },
  'Index of Terms water_extract_biosolid': { folder: 'IoT_water_extract_biosolid', status: 'published' },
  'Index of Terms water_extract_soil': { folder: 'IoT_water_extract_soil', status: 'published' },
};

export function useHarmonizerApi(element: Ref<HTMLIFrameElement>) {
  const validationErrors = ref({} as Record<number, Record<number, string>>);
  const schemaFields = ref([] as string[]);

  function setupTemplate(folder: string) {
    element.value.contentWindow?.postMessage({ type: 'setupTemplate', folder });
  }

  function validate() {
    element.value.contentWindow?.postMessage({ type: 'validate' });
  }

  function subscribe() {
    window.addEventListener('message', (event) => {
      // console.log('Received message from child window', event.data.type);
      if (event.data.type === 'update') {
        // @ts-ignore
        validationErrors.value = element.value.contentWindow?.INVALID_CELLS;
      }
    });
  }

  subscribe();

  return {
    validationErrors,
    schemaFields,
    /* Methods */
    setupTemplate,
    validate,
  };
}
