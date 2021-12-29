import { ref, Ref } from '@vue/composition-api';

export const IFRAME_BASE = process.env.NODE_ENV === 'development' ? '' : 'https://microbiomedata.github.io/';

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

  function jumpTo(columnName: string) {
    element.value.contentWindow?.postMessage({ type: 'jumpTo', columnName });
  }

  function jumpToRowCol(row: number, column: number) {
    element.value.contentWindow?.postMessage({ type: 'jumpToRowCol', row, column });
  }

  function setupTemplate(folder: string) {
    element.value.contentWindow?.postMessage({ type: 'setupTemplate', folder });
  }

  function validate() {
    element.value.contentWindow?.postMessage({ type: 'validate' });
  }

  function openFile() {
    element.value.contentWindow?.postMessage({ type: 'open' });
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
