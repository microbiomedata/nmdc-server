import {
  watch, Ref, computed, toRef, shallowReactive,
} from '@vue/composition-api';
import {
  SearchParams, Condition, DataObjectFilter, SearchResponse,
} from '@/data/api';
import useRequest from './useRequest';

export default function usePaginatedResult<T>(
  conditions: Ref<Condition[]>,
  func: (param: SearchParams) => Promise<SearchResponse<T>>,
  dataObjectFilter?: Ref<DataObjectFilter[]>,
  limit = 15,
) {
  const data = shallowReactive({
    results: { count: 0, results: [] } as SearchResponse<T>,
    offset: 0,
    limit, // same as pageSize
    pageSync: 1,
  });
  const { error, loading, request } = useRequest();

  const page = computed(() => {
    const { offset, limit: l } = data;
    // Add one for 1-indexed page
    return Math.floor(offset / l) + 1;
  });

  // TODO replace with watchEffect
  async function fetchResults() {
    return request(async () => {
      data.results = await func({
        limit: data.limit,
        offset: data.offset,
        conditions: conditions.value,
        data_object_filter: dataObjectFilter?.value,
      });
      data.pageSync = Math.floor(data.offset / data.limit) + 1;
      return data.results;
    });
  }

  watch([
    toRef(data, 'limit'),
    toRef(data, 'offset'),
  ], fetchResults);
  watch([conditions], () => {
    const doFetch = data.offset === 0;
    data.offset = 0;
    data.limit = limit;
    if (doFetch) fetchResults();
  });

  if (dataObjectFilter !== undefined) {
    watch(dataObjectFilter, fetchResults, { deep: true });
  }
  fetchResults();
  // ENDTODO

  function setPage(newPage: number) {
    data.offset = (newPage - 1) * data.limit;
  }

  function setItemsPerPage(newLimit: number) {
    data.limit = newLimit;
  }

  return {
    data,
    error,
    loading,
    page,
    setPage,
    setItemsPerPage,
  };
}
