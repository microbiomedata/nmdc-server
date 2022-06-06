declare module '*.vue' {
  import Vue from 'vue';

  export default Vue;
}

// HACK-DH
declare module '*.html' {
  const value: string;
  export default value;
}

declare const DataHarmonizer: any;
declare const TEMPLATES: any;
declare const SCHEMA: any;
declare function $(...args: any[]): any;
