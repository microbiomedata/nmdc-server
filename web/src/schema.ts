import NmdcSchema from 'nmdc-schema/nmdc_schema/nmdc_materialized_patterns.json';

const doiProviderValues = Object.values(NmdcSchema.enums.DoiProviderEnum.permissible_values)
  .map((pv: any) => ({
    value: pv.text,
    text: pv.title || pv.text, // The permissible value definition should have a title, but in case it doesn't fallback to text (which it will always have)
  }))
  .sort((a, b) => a.text.localeCompare(b.text));

export default doiProviderValues;
