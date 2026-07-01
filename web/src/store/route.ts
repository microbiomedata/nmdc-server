import { RouteLocationNormalizedLoaded } from 'vue-router';

function routeHasConditions(currentRoute: Pick<RouteLocationNormalizedLoaded, 'query'>) {
  const { conditions } = currentRoute.query;
  return Array.isArray(conditions) ? conditions.length > 0 : !!conditions;
}

export { routeHasConditions };
