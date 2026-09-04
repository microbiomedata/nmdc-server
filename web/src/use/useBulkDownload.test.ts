import { nextTick, ref } from 'vue';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import type {
  BulkDownloadAggregateSummary, BulkDownloadSummary, Condition, DataObjectFilter,
} from '@/data/api';
import useBulkDownload from './useBulkDownload';

const apiMocks = vi.hoisted(() => ({
  createBulkDownload: vi.fn(),
  getBulkDownloadAggregateSummary: vi.fn(),
  getBulkDownloadSummary: vi.fn(),
}));

vi.mock('@/data/api', () => ({ api: apiMocks }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolvePromise) => {
    resolve = resolvePromise;
  });
  return { promise, resolve };
}

describe('useBulkDownload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('does not replace filtered results with an older unfiltered response', async () => {
    const oldOptions = deferred<BulkDownloadSummary>();
    const filteredOptions = deferred<BulkDownloadSummary>();
    const oldSummary = deferred<BulkDownloadAggregateSummary>();
    const filteredSummary = deferred<BulkDownloadAggregateSummary>();
    apiMocks.getBulkDownloadSummary
      .mockReturnValueOnce(oldOptions.promise)
      .mockReturnValueOnce(filteredOptions.promise);
    apiMocks.getBulkDownloadAggregateSummary
      .mockReturnValueOnce(oldSummary.promise)
      .mockReturnValueOnce(filteredSummary.promise);

    const conditions = ref<Condition[]>([]);
    const dataObjectFilter = ref<DataObjectFilter[]>([]);
    const bulkDownload = useBulkDownload(conditions, dataObjectFilter);

    conditions.value = [{
      field: 'id', op: 'like', table: 'biosample', value: 'nmdc:bsm-11-dx77v768',
    }];
    await nextTick();

    const expectedOptions: BulkDownloadSummary = {
      Assembly: { count: 1, size: 10, file_types: {} },
    };
    filteredOptions.resolve(expectedOptions);
    filteredSummary.resolve({ count: 1, size: 10 });
    await nextTick();

    oldOptions.resolve({ Assembly: { count: 4272, size: 99999, file_types: {} } });
    oldSummary.resolve({ count: 4272, size: 99999 });
    await nextTick();

    expect(bulkDownload.downloadOptions.value).toEqual(expectedOptions);
    expect(bulkDownload.downloadSummary.value).toEqual({ count: 1, size: 10 });
  });
});
