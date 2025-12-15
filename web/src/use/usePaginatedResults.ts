import {
  watch, Ref, computed, shallowReactive,
} from 'vue';
import { debounce } from 'lodash';
import {
  SearchParams, Condition, DataObjectFilter, SearchResponse,
} from '@/data/api';
import useRequest from './useRequest';

export interface PaginatedResult<T> {
  data: {
    results: SearchResponse<T>;
    offset: number;
    limit: number;
    sortColumn: string;
    sortOrder: string;
    pageSync: number;
  };
  error: Ref<string | null>;
  loading: Ref<boolean>;
  page: Ref<number>;
  refetch: () => Promise<SearchResponse<T> | void>;
  setPage: (newPage: number) => void;
  setItemsPerPage: (newLimit: number) => void;
  setSortOptions: (columnSort: string, sortOrder: string) => void;
  fetchCount: Ref<number>;
  reset: () => void;
}

export default function usePaginatedResult<T>(
  conditions: Ref<Condition[]>,
  func: (param: SearchParams) => Promise<SearchResponse<T>>,
  dataObjectFilter?: Ref<DataObjectFilter[]>,
  limit = 15,
  enabled: Ref<boolean> = computed(() => true),
): PaginatedResult<T> {
  const data = shallowReactive({
    results: { count: 0, results: [] } as SearchResponse<T>,
    offset: 0,
    limit, // same as pageSize
    sortColumn: '',
    sortOrder: 'desc',
    pageSync: 1,
  });
  const {
    error,
    loading,
    count,
    request,
    reset: requestReset,
  } = useRequest();

  const page = computed(() => {
    const { offset, limit: l } = data;
    // Add one for 1-indexed page
    return Math.floor(offset / l) + 1;
  });

  // TODO replace with watchEffect
  async function fetchResults() {
    if (!enabled.value) {
      return;
    }
    await request(async () => {
      data.results = await func({
        limit: data.limit,
        offset: data.offset,
        sortColumn: data.sortColumn,
        sortOrder: data.sortOrder,
        conditions: conditions.value,
        data_object_filter: dataObjectFilter?.value,
      });
      data.pageSync = Math.floor(data.offset / data.limit) + 1;
    });
  }

  const debouncedFetchResults = debounce(fetchResults, 500);

  watch([conditions], () => {
    const doFetch = data.offset === 0;
    data.offset = 0;
    if (doFetch) {
      debouncedFetchResults();
    }
  });

  if (dataObjectFilter !== undefined) {
    watch(dataObjectFilter, debouncedFetchResults, { deep: true });
  }
  debouncedFetchResults();
  // ENDTODO

  function setPage(newPage: number) {
    data.offset = (newPage - 1) * data.limit;
    debouncedFetchResults();
  }

  function setItemsPerPage(newLimit: number) {
    data.limit = newLimit;
    data.offset = Math.floor(data.offset / newLimit) * newLimit;
    debouncedFetchResults();
  }

  function setSortOptions(columnSort: string, sortOrder: string) {
    data.sortColumn = columnSort;
    data.sortOrder = sortOrder;
    debouncedFetchResults();
  }

  function reset() {
    requestReset();
    data.results = { count: 0, results: [] } as SearchResponse<T>;
    data.offset = 0;
    data.limit = limit;
    data.sortColumn = '';
    data.sortOrder = 'desc';
    data.pageSync = 1;
  }

  return {
    data,
    error,
    fetchCount: count,
    loading,
    page,
    reset,
    refetch: fetchResults,
    setPage,
    setItemsPerPage,
    setSortOptions,
  };
}
