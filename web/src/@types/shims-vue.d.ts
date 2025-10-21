declare module '*.vue' {
  import Vue from 'vue';

  export default Vue;
}

declare module '@microbiomedata/data-harmonizer';
declare function $(...args: any[]): any;

declare module "*.png" {
  const value: string;
  export default value;
}