import {
  reactive, toRef, watch, Ref, computed,
} from '@vue/composition-api';
import { SearchParams, ResultUnion, Condition } from '@/data/api';

export default function usePaginatedResult(
  conditions: Ref<Condition[]>,
  func: (param: SearchParams) => Promise<ResultUnion>,
  limit = 15,
) {
  const data = reactive({
    results: { count: 0, results: [] } as ResultUnion,
    offset: 0,
    limit, // same as pageSize
    pageSync: 1,
  });

  const page = computed(() => {
    const { offset, limit: l } = data;
    // Add one for 1-indexed page
    return Math.floor(offset / l) + 1;
  });

  // TODO replace with watchEffect
  async function fetchResults() {
    data.results = await func({
      limit: data.limit,
      offset: data.offset,
      conditions: conditions.value,
    });
    data.pageSync = Math.floor(data.offset / data.limit) + 1;
  }
  watch([conditions, toRef(data, 'offset'), toRef(data, 'limit')], fetchResults);
  fetchResults();
  // ENDTODO

  function setPage(newPage: number) {
    data.offset = (newPage - 1) * data.limit;
  }

  return {
    data,
    page,
    setPage,
  };
}
