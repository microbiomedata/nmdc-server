# NMDC pilot

An early prototype system for NMDC.

**Note:** This early proof of concept is for collecting feedback on query,
interaction, and visualization features for NMDC, not for any kind of real use. In particular,
there is no access to the full raw data files, there is no login or ingestion, and there are no
associated analytics. All data models and interfaces are subject to change. 

## Client architecture

This client uses Vue, Vuex, and Vue router together to manage query state.  All the state needed to load a page should come from the route parameters and query string, and supplemental state inside Vuex can be thought of as simply a caching layer.

This app uses `vuex-router-sync` so that Vuex getters and actions can treat the route as part of its state.  It uses a `router.afterEach` handler so that route changes that should cause some side-effect in the cache can dispatch actions.

* code in `src/components` is "functional": it relies only on the state of its props, and produces no side-effects other than emitted events.
* code in `src/views` makes use of vuex and the api shims.

Some components, like `src/views/Search/FilterList` use lazy-load of data that could have been prefetched based on the state of the store and router.  It does so using its own lifecycle hooks: It will dispatch an action to load and cache facet results when it gets created, then listen for global cache invalidations (caused primarily by routing changes) to re-fetch.  That specific component is the dialog content from a `v-menu`, which used to have native support for lazy-rendering, but now uses `v-if="isOpen"` to achieve the same effect since support was dropped in Vuetify.

## Project setup
```
yarn install
```

### Compiles and hot-reloads for development on http://localhost:8080
```
yarn serve
```

### Compiles and minifies for production
```
yarn build
```

### Lints and fixes files
```
yarn lint
```

### Deploy to github.io
```
./deploy.sh
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
