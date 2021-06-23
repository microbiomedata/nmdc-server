import {
  reactive, watch, Ref, computed, toRef,
} from '@vue/composition-api';
import {
  SearchParams, ResultUnion, Condition, DataObjectFilter,
} from '@/data/api';
import useRequest from './useRequest';

export default function usePaginatedResult(
  conditions: Ref<Condition[]>,
  func: (param: SearchParams) => Promise<ResultUnion>,
  dataObjectFilter?: Ref<DataObjectFilter[]>,
  limit = 15,
) {
  const data = reactive({
    results: { count: 0, results: [] } as ResultUnion,
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
    conditions,
    toRef(data, 'offset'),
    toRef(data, 'limit'),
  ], fetchResults);
  if (dataObjectFilter !== undefined) {
    watch(dataObjectFilter, fetchResults, { deep: true });
  }
  fetchResults();
  // ENDTODO

  function setPage(newPage: number) {
    data.offset = (newPage - 1) * data.limit;
  }

  return {
    data,
    error,
    loading,
    page,
    setPage,
  };
}
