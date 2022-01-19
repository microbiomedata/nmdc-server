import { ref, Ref } from '@vue/composition-api';

export const IFRAME_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:3333/' : 'https://microbiomedata.github.io/DataHarmonizer';
// export const IFRAME_BASE = 'https://microbiomedata.github.io/';

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES = {
  air: { folder: '', status: 'disabled' },
  'built environment': { folder: '', status: 'disabled' },
  'host-associated': { folder: '', status: 'disabled' },
  'human-associated': { folder: '', status: 'disabled' },
  'human-gut': { folder: '', status: 'disabled' },
  'human-oral': { folder: '', status: 'disabled' },
  'human-skin': { folder: '', status: 'disabled' },
  'human-vaginal': { folder: '', status: 'disabled' },
  'hydrocarbon resources-cores': { folder: '', status: 'disabled' },
  'hydrocarbon resources-fluids_swabs': { folder: '', status: 'disabled' },
  'microbial mat_biofilm': { folder: '', status: 'disabled' },
  'miscellaneous natural or artificial environment': { folder: '', status: 'disabled' },
  'plant-associated': { folder: '', status: 'disabled' },
  sediment: { folder: '', status: 'disabled' },
  soil: { folder: 'dev', status: 'published' },
  wastewater_sludge: { folder: '', status: 'disabled' },
  water: { folder: '', status: 'disabled' },
};

export function useHarmonizerApi(element: Ref<HTMLIFrameElement>) {
  const validationErrors = ref(undefined as undefined | null | Record<number, Record<number, string>>);
  const schemaFields = ref([] as string[]);

  /* Promises for async methods */
  let validationPromiseResolvers: ((valid: boolean) => void)[] = [];
  let exportJsonPromiseResolvers: ((data: object) => void)[] = [];

  const postMessage = (message: any) => element.value.contentWindow?.postMessage(message, '*');

  function changeVisibility(value: string) {
    postMessage({ type: 'changeVisibility', value });
  }

  function jumpTo(columnName: string) {
    postMessage({ type: 'jumpTo', columnName });
  }

  function jumpToRowCol(row: number, column: number) {
    postMessage({ type: 'jumpToRowCol', row, column });
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

  function openFile(files: File[]) {
    postMessage({ type: 'open', files });
  }

  function exportJson() {
    return new Promise<object>((resolve) => {
      exportJsonPromiseResolvers.push(resolve);
      postMessage({ type: 'exportJson' });
    });
  }

  function exportTable() {
    postMessage({ type: 'exportTable' });
  }

  function subscribe() {
    window.addEventListener('message', (event) => {
      if (event.data.type === 'update') {
        validationErrors.value = event.data.INVALID_CELLS;
        schemaFields.value = event.data.fieldYCoordinates;
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
    schemaFields,
    /* Methods */
    changeVisibility,
    exportJson,
    exportTable,
    jumpTo,
    jumpToRowCol,
    openFile,
    setupTemplate,
    validate,
  };
}
