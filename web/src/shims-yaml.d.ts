import { NmdcSchema } from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.yaml';
declare module '*.yaml' {
  const value: Record<string, any>;
  export default value;
}
declare module '*.yml' {
  const value: Record<string, any>;
  export default value;
}
