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
) {
  const downloadOptions = ref({} as BulkDownloadSummary);
  const bulkDownloads = ref([] as BulkDownload[]);
  const { loading, error, request } = useRequest();
  const downloadSummary = ref({
    count: 0,
    size: 0,
  } as BulkDownloadAggregateSummary);

  async function download() {
    return request(async () => {
      const val = await api.createBulkDownload(conditions.value, dataObjectFilter.value);
      bulkDownloads.value.push(val);
      return val;
    });
  }

  async function getSummary() {
    downloadSummary.value = await api.getBulkDownloadAggregateSummary(
      conditions.value,
      dataObjectFilter.value,
    );
  }

  async function getDownloadOptions() {
    downloadOptions.value = await api.getBulkDownloadSummary(conditions.value);
  }

  watch([conditions, dataObjectFilter], getSummary);
  watch([conditions], getDownloadOptions);

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
