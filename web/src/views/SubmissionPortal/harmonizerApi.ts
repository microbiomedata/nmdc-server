import { ref, Ref } from '@vue/composition-api';

export const IFRAME_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:3333/' : 'https://microbiomedata.github.io/DataHarmonizer';
// export const IFRAME_BASE = 'https://microbiomedata.github.io/';

/**
 * A manifest of the options available in DataHarmonizer
 */
export const HARMONIZER_TEMPLATES = {
  'MAM NMDC Dev Template': { folder: 'dev', status: 'published' },
  'CanCOGeN Covid-19': { folder: 'canada_covid19', status: 'published' },
  'PHAC Dexa (ALPHA)': { folder: 'phac_dexa', status: 'draft' },
  'GRDI (ALPHA)': { folder: 'grdi', status: 'draft' },
  'GISAID (ALPHA)': { folder: 'gisaid', status: 'draft' },
  PHA4GE: { folder: 'pha4ge', status: 'published' },
};

export function useHarmonizerApi(element: Ref<HTMLIFrameElement>) {
  const validationErrors = ref(undefined as undefined | null | Record<number, Record<number, string>>);
  const schemaFields = ref([] as string[]);

  const postMessage = (message: any) => element.value.contentWindow?.postMessage(message, '*');

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
    postMessage({ type: 'validate' });
  }

  function openFile(files: File[]) {
    postMessage({ type: 'open', files });
  }

  function subscribe() {
    window.addEventListener('message', (event) => {
      if (event.data.type === 'update') {
        validationErrors.value = event.data.INVALID_CELLS;
        schemaFields.value = event.data.fieldYCoordinates;
      }
    });
  }

  subscribe();

  return {
    validationErrors,
    schemaFields,
    /* Methods */
    jumpTo,
    jumpToRowCol,
    openFile,
    setupTemplate,
    validate,
  };
}
