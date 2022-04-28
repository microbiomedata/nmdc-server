import { ref, Ref } from '@vue/composition-api';

export const IFRAME_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:3333' : 'https://microbiomedata.github.io/sheets_and_friends';
// export const IFRAME_BASE = 'https://microbiomedata.github.io/sheets_and_friends';

const VariationMap = {
  /** A mapping of the templates to the superset of checkbox options they work for. */
  emsl: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl']),
  jgi_mg: new Set(['mg-jgi']),
  emsl_jgi_mg: new Set(['mp-emsl', 'mb-emsl', 'nom-emsl', 'mg-jgi']),
};

export function getVariant(checkBoxes: string[], variations: (keyof typeof VariationMap)[], base: string) {
  const variationStr = variations.find((v) => {
    const vSet = VariationMap[v];
    return checkBoxes.every((elem) => vSet.has(elem));
  });
  if (variationStr) {
    return `${base}_${variationStr}`;
  }
  return base;
}

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES: Record<string, {
  default: string;
  status: String;
  variations: (keyof typeof VariationMap)[];
}> = {
  air: { default: 'air', status: 'published', variations: [] },
  'built environment': { default: 'built_env', status: 'published', variations: [] },
  'host-associated': { default: 'host-associated', status: 'published', variations: [] },
  'human-associated': { default: '', status: 'disabled', variations: [] },
  'human-gut': { default: '', status: 'disabled', variations: [] },
  'human-oral': { default: '', status: 'disabled', variations: [] },
  'human-skin': { default: '', status: 'disabled', variations: [] },
  'human-vaginal': { default: '', status: 'disabled', variations: [] },
  'hydrocarbon resources-cores': {
    default: 'hcr-cores', status: 'published', variations: [],
  },
  'hydrocarbon resources-fluids_swabs': {
    default: 'hcr-fluids-swabs', status: 'published', variations: [],
  },
  'microbial mat_biofilm': {
    default: 'biofilm', status: 'published', variations: [],
  },
  'miscellaneous natural or artificial environment': {
    default: 'misc-envs', status: 'published', variations: [],
  },
  'plant-associated': {
    default: 'plant-associated', status: 'published', variations: [],
  },
  sediment: {
    default: 'sediment', status: 'published', variations: [],
  },
  soil: {
    default: 'soil', status: 'published', variations: ['emsl', 'emsl_jgi_mg', 'jgi_mg'],
  },
  wastewater_sludge: {
    default: 'wastewater_sludge', status: 'published', variations: [],
  },
  water: {
    default: 'water', status: 'published', variations: [],
  },
};

export function useHarmonizerApi(element: Ref<HTMLIFrameElement>) {
  const validationErrors = ref(undefined as undefined | null | Record<number, Record<number, string>>);
  const schemaSections = ref({} as Record<string, Record<string, number>>);
  const ready = ref(false);
  /* Promises for async methods */
  let validationPromiseResolvers: ((valid: boolean) => void)[] = [];
  let exportJsonPromiseResolvers: ((data: any[][]) => void)[] = [];

  const postMessage = (message: any) => element.value.contentWindow?.postMessage(message, '*');

  function changeVisibility(value: string) {
    postMessage({ type: 'changeVisibility', value });
  }

  function exportJson() {
    return new Promise<any[][]>((resolve) => {
      exportJsonPromiseResolvers.push(resolve);
      postMessage({ type: 'exportJson' });
    });
  }

  function exportTable() {
    postMessage({ type: 'exportTable' });
  }

  function jumpTo(columnName: string) {
    postMessage({ type: 'jumpTo', columnName });
  }

  function jumpToRowCol(row: number, column: number) {
    postMessage({ type: 'jumpToRowCol', row, column });
  }

  function launchReference() {
    postMessage({ type: 'showReference' });
  }

  function loadData(data: any[][]) {
    ready.value = false;
    postMessage({ type: 'loadData', data });
  }

  function openFile(files: File[]) {
    postMessage({ type: 'open', files });
  }

  function setupTemplate(folder: string) {
    postMessage({ type: 'setupTemplate', folder });
  }

  function validate() {
    return new Promise<boolean>((resolve) => {
      validationPromiseResolvers.push(resolve);
      postMessage({ type: 'validate' });
    });
  }

  function subscribe() {
    window.addEventListener('message', (event) => {
      if (event.data.type === 'update') {
        validationErrors.value = event.data.INVALID_CELLS;
        schemaSections.value = event.data.columnCoordinates;
        validationPromiseResolvers.forEach((resolve) => resolve(Object.keys(event.data.INVALID_CELLS || {}).length === 0));
        validationPromiseResolvers = [];
        ready.value = true;
      } else if (event.data.type === 'exportJson') {
        exportJsonPromiseResolvers.forEach((resolve) => resolve(event.data.value));
        exportJsonPromiseResolvers = [];
      }
    });
  }

  subscribe();

  return {
    validationErrors,
    ready,
    schemaSections,
    /* Methods */
    changeVisibility,
    exportJson,
    exportTable,
    jumpTo,
    jumpToRowCol,
    launchReference,
    loadData,
    openFile,
    setupTemplate,
    validate,
  };
}
