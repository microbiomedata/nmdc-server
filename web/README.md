# NMDC Data Portal

## Client architecture

Some components, like `src/views/Search/FilterList` use lazy-load of data that could have been prefetched based on the state of the store and router.  It does so using its own lifecycle hooks: It will dispatch an action to load and cache facet results when it gets created, then listen for global cache invalidations (caused primarily by routing changes) to re-fetch.  That specific component is the dialog content from a `v-menu`, which used to have native support for lazy-rendering, but now uses `v-if="isOpen"` to achieve the same effect since support was dropped in Vuetify.

### Organization

* `components/Presentation` should make no api calls and should not import state.  They are pure presentation.
* `components/Wrappers` temporarily wrap mixins until these are converted to composition functions.
* `store/` should contain global singleton Vue3 style reactive data.  This is not Vuex.
* `use/` is for composition functions, which may make API calls, but may NOT import state.
* `views/` is for application code that combines `use`, `store`, and `components`.

## Stateless requests

This application serves data from a stateless database, so queries can be cached, and many requests only need to be loaded once.
