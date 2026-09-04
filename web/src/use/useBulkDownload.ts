import { Ref, ref, watch } from 'vue';
import {
  api, BulkDownload, BulkDownloadAggregateSummary, BulkDownloadSummary, Condition, DataObjectFilter,
} from '@/data/api';
import useRequest from './useRequest';

/**
 * Encapsulates API and state for bulk download.
 */
export default function useBulkDownload(
  conditions: Ref<Condition[]>,
  dataObjectFilter: Ref<DataObjectFilter[]>,
  includeSupersededWorkflowExecutions: Ref<boolean> = ref(false),
) {
  const downloadOptions = ref({} as BulkDownloadSummary);
  const bulkDownloads = ref([] as BulkDownload[]);
  const { loading, error, request } = useRequest();
  const downloadSummary = ref({
    count: 0,
    size: 0,
  } as BulkDownloadAggregateSummary);

  async function download() {
    const val = await request(async () => {
      const result = await api.createBulkDownload(
        conditions.value,
        dataObjectFilter.value,
        includeSupersededWorkflowExecutions.value,
      );
      bulkDownloads.value.push(result);
      return result;
    });
    if (error.value) {
      throw new Error(error.value);
    }
    return val;
  }

  watch([conditions, dataObjectFilter, includeSupersededWorkflowExecutions], async (_value, _oldValue, onCleanup) => {
    let stale = false;
    onCleanup(() => {
      stale = true;
    });
    const summary = await api.getBulkDownloadAggregateSummary(
      conditions.value,
      dataObjectFilter.value,
      includeSupersededWorkflowExecutions.value,
    );
    if (!stale) {
      downloadSummary.value = summary;
    }
  }, { immediate: true });

  watch([conditions, includeSupersededWorkflowExecutions], async (_value, _oldValue, onCleanup) => {
    let stale = false;
    onCleanup(() => {
      stale = true;
    });
    const options = await api.getBulkDownloadSummary(
      conditions.value,
      includeSupersededWorkflowExecutions.value,
    );
    if (!stale) {
      downloadOptions.value = options;
    }
  }, { immediate: true });

  return {
    bulkDownloads,
    downloadOptions,
    downloadSummary,
    error,
    loading,
    download,
  };
}
