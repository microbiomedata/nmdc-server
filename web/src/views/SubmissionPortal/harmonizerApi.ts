import { ref, Ref } from '@vue/composition-api';

// export const IFRAME_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:3333' : 'https://deploy-preview-101--voluble-pika-79eed4.netlify.app';
export const IFRAME_BASE = 'https://deploy-preview-101--voluble-pika-79eed4.netlify.app/';

const StandardVariations = [
  'emsl',
  'emsl_jgi_mg',
  'emsl_jgi_mt',
  'jgi_mg',
  'jgi_mt',
];

export function getVariant(checkBoxes: string[], variations: string[], base: string) {
  let emsl = false;
  let jgi = false;
  let mt = false;
  let mg = false;

  checkBoxes.forEach((option) => {
    if (option.endsWith('-emsl')) {
      emsl = true;
    }
    if (option.endsWith('-jgi')) {
      jgi = true;
    }
    if (option.startsWith('mt-')) {
      mt = true;
    }
    if (option.startsWith('mg-')) {
      mg = true;
    }
  });

  const variation = [];

  if (emsl) {
    variation.push('emsl');
  }
  if (jgi) {
    variation.push('jgi');
  }
  if (mg) {
    variation.push('mg');
  }
  if (mt) {
    variation.push('mt');
  }

  const variationStr = variation.join('_');

  if (variations.includes(variationStr)) {
    return `${base}_${variationStr}`;
  }

  if (variation.length === 0) {
    return base;
  }

  throw new Error(`No variation of ${base} with ${variationStr}`);
}

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES = {
  air: { default: '', status: 'disabled', variations: [] },
  biofilm: { default: 'biofilm', status: 'enabled', variations: [] },
  'built environment': { default: 'built_env', status: 'enabled', variations: [] },
  'host-associated': { default: '', status: 'disabled', variations: [] },
  'human-associated': { default: '', status: 'disabled', variations: [] },
  'human-gut': { default: '', status: 'disabled', variations: [] },
  'human-oral': { default: '', status: 'disabled', variations: [] },
  'human-skin': { default: '', status: 'disabled', variations: [] },
  'human-vaginal': { default: '', status: 'disabled', variations: [] },
  'hydrocarbon resources-cores': { default: '', status: 'disabled', variations: [] },
  'hydrocarbon resources-fluids_swabs': { default: '', status: 'disabled', variations: [] },
  'microbial mat_biofilm': { default: '', status: 'disabled', variations: [] },
  'miscellaneous natural or artificial environment': {
    default: '', status: 'disabled', variations: [],
  },
  'plant-associated': { default: '', status: 'disabled', variations: [] },
  sediment: { default: '', status: 'disabled', variations: [] },
  soil: {
    default: 'soil',
    status: 'published',
    variations: StandardVariations,
  },
  wastewater_sludge: { default: '', status: 'disabled', variations: [] },
  water: { default: '', status: 'disabled', variations: [] },
};

export function useHarmonizerApi(element: Ref<HTMLIFrameElement>) {
  const validationErrors = ref(undefined as undefined | null | Record<number, Record<number, string>>);
  const schemaSections = ref({} as Record<string, Record<string, number>>);

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

  function loadData(data: any[][]) {
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
      } else if (event.data.type === 'exportJson') {
        exportJsonPromiseResolvers.forEach((resolve) => resolve(event.data.value));
        exportJsonPromiseResolvers = [];
      }
    });
  }

  subscribe();

  return {
    validationErrors,
    schemaSections,
    /* Methods */
    changeVisibility,
    exportJson,
    exportTable,
    jumpTo,
    jumpToRowCol,
    loadData,
    openFile,
    setupTemplate,
    validate,
  };
}
