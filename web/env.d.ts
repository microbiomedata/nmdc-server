/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />

declare module '*.yaml' {
  const content: any;
  export default content;
}

declare module '*.yml' {
  const content: any;
  export default content;
}
