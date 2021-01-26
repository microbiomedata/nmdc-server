# Search V2

A second version of the NMDC Search interface.  Parts of the old interface may be rewritten or duplicated here.

## Goals

* 100% typescript
* less generic behavior

## Organization

* `components/` should make no api calls and should not import state.  They are pure presentation.
* `store/` should contain global singleton Vue3 style reactive data.  This is not Vuex.
* `use/` is for composition functions, which may make API calls, but may NOT import state.
* `views/` is for application code that combines `use`, `store`, and `components`.
