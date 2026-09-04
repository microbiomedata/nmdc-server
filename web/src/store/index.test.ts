import { describe, expect, test } from 'vitest';
import type { Router } from 'vue-router';
import type { Condition } from '@/data/api';
import { initializeRouteState, stateRefs } from './index';

describe('initializeRouteState', () => {
  test('hydrates conditions from the parsed route synchronously', () => {
    const conditions: Condition[] = [{
      field: 'id', op: 'like', table: 'biosample', value: 'nmdc:bsm-11-dx77v768',
    }];
    const router = {
      currentRoute: { value: { query: { conditions } } },
    } as unknown as Router;

    initializeRouteState(router);

    expect(stateRefs.conditions.value).toEqual(conditions);
  });
});
