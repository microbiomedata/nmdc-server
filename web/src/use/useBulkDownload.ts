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

  async function getSummary() {
    downloadSummary.value = await api.getBulkDownloadAggregateSummary(
      conditions.value,
      dataObjectFilter.value,
      includeSupersededWorkflowExecutions.value,
    );
  }

  async function getDownloadOptions() {
    console.log('Re-fetching download options with conditions:', conditions.value, 'and includeSupersededWorkflowExecutions:', includeSupersededWorkflowExecutions.value);
    downloadOptions.value = await api.getBulkDownloadSummary(
      conditions.value,
      includeSupersededWorkflowExecutions.value,
    );
  }

  watch([conditions, dataObjectFilter, includeSupersededWorkflowExecutions], getSummary);
  watch([conditions, includeSupersededWorkflowExecutions], getDownloadOptions);

  getDownloadOptions();
  getSummary();

  return {
    bulkDownloads,
    downloadOptions,
    downloadSummary,
    error,
    loading,
    download,
  };
}
