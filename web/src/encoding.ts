import colors from './colors';
import { entityType, entitySchemaType } from './data/api';

export interface EntityData {
  icon: string;
  heading: string;
  name: string;
  plural: string;
  visible: boolean;
  schemaName?: entitySchemaType; // Match the table to the NMDC Schema definition
}

export interface FieldsData {
  icon?: string;
  hideFacet?: boolean;
  sortKey?: number;
  name?: string;
  description?: string[];
  group?: string;
  hideAttr?: boolean;
  schemaName?: string; // Match the field to the nmsc schema property
  encode?: (input: string) => string,
}

const KeggPrefix = {
  ORTHOLOGY: {
    pattern: /^((ko?:?)|(kegg\.orthology:))(?=\d{5})/i,
    short: 'K',
    long: 'KEGG.ORTHOLOGY:K',
  },
  PATHWAY: {
    pattern: /^((map:?)|(path:?)|(kegg.pathway:))(?=\d{5})/i,
    short: 'MAP',
    long: 'KEGG.PATHWAY:MAP',
  },
  MODULE: {
    pattern: /^((m:?)|(kegg.module:))(?=\d{5})/i,
    short: 'M',
    long: 'KEGG.MODULE:M',
  },
};
/**
 * Encode a string as either the long or short variant of
 * a KEGG identifier term.
 */
function keggEncode(v: string, useLong = true) {
  const prefixes = Object.values(KeggPrefix);
  for (let i = 0; i < prefixes.length; i += 1) {
    const { pattern, short, long } = prefixes[i];
    const transformed = v.replace(pattern, useLong ? long : short);
    if (transformed !== v) return transformed;
  }
  return v;
}

function stringIsKegg(v: string) {
  return Object.values(KeggPrefix).find((item) => v.match(item.pattern));
}

const types: Record<entityType, EntityData> = {
  study: {
    icon: 'mdi-book',
    heading: 'Studies',
    name: 'study',
    plural: 'studies',
    visible: true,
    schemaName: 'Study',
  },
  omics_processing: {
    icon: 'mdi-file-table-box-multiple-outline',
    heading: 'Omics Types',
    name: 'omics_processing',
    plural: 'Omics Processing',
    visible: true,
    schemaName: 'OmicsProcessing',
  },
  biosample: {
    icon: 'mdi-test-tube',
    heading: 'Environments',
    name: 'sample',
    plural: 'samples',
    visible: true,
    schemaName: 'Biosample',
  },
  reads_qc: {
    icon: 'mdi-dna',
    heading: 'Reads QC',
    name: 'reads_qc',
    plural: 'Reads QC',
    visible: true,
  },
  metagenome_assembly: {
    icon: 'mdi-dna',
    heading: 'Metagenome Assembly',
    name: 'metagenome_assembly',
    plural: 'Metagenome assembly',
    visible: true,
    schemaName: 'MetagenomeAssembly',
  },
  metagenome_annotation: {
    icon: 'mdi-dna',
    heading: 'Metagenome Annotation',
    name: 'metagenome_annotation',
    plural: 'Metagenome annotation',
    visible: true,
    schemaName: 'MetagenomeAnnotationActivity',
  },
  metaproteomic_analysis: {
    icon: 'mdi-dna',
    heading: 'Metaproteomic Analysis',
    name: 'metaproteomic_analysis',
    plural: 'Metaproteomic analysis',
    visible: true,
    schemaName: 'MetaproteomicsAnalysisActivity',
  },
  data_object: {
    icon: 'mdi-database',
    heading: 'Data Object',
    name: 'data_object',
    plural: 'Data objects',
    visible: false,
    schemaName: 'DataObject',
  },
  gene_function: {
    icon: 'mdi-dna',
    heading: 'Gene Function',
    name: 'gene_function',
    plural: 'Gene functions',
    visible: true,
  },
};

const fields: Record<string, FieldsData> = {
  id: {
    icon: 'mdi-key',
    hideFacet: true,
  },
  study_id: {
    icon: 'mdi-key-link',
    hideFacet: true,
  },
  omics_processing_id: {
    icon: 'mdi-key-link',
    hideFacet: true,
    sortKey: 0,
  },
  git_url: {
    icon: 'mdi-git',
    hideFacet: true,
  },
  location: {
    icon: 'mdi-earth',
    hideFacet: true,
  },
  latitude: {
    icon: 'mdi-earth',
    hideFacet: false,
    sortKey: 1,
  },
  longitude: {
    icon: 'mdi-earth',
    hideFacet: false,
    sortKey: 2,
  },
  identifier: {
    icon: 'mdi-text',
    hideFacet: true,
  },
  file_size: {
    icon: 'mdi-text',
    hideFacet: true,
  },
  description: {
    icon: 'mdi-text',
    hideFacet: true,
  },
  depth: {
    icon: 'mdi-tape-measure',
    sortKey: 0,
  },
  sample_collection_site: {
    icon: 'mdi-earth',
    hideFacet: true,
  },
  geo_loc_name: {
    name: 'Geographic Location Name',
    icon: 'mdi-earth',
    sortKey: 3,
  },
  add_date: {
    icon: 'mdi-calendar',
    hideFacet: true,
    hideAttr: true,
  },
  mod_date: {
    icon: 'mdi-calendar',
    name: 'Modification Date',
    hideFacet: true,
    hideAttr: true,
  },
  collection_date: {
    icon: 'mdi-calendar',
  },
  ecosystem_path_id: {
    icon: 'mdi-pine-tree',
    hideFacet: true,
  },
  habitat: {
    icon: 'mdi-pine-tree',
    hideFacet: true,
  },
  community: {
    icon: 'mdi-google-circles-communities',
    hideFacet: true,
  },
  principal_investigator_name: {
    name: 'PI Name',
    icon: 'mdi-account',
    schemaName: 'principal_investigator',
  },
  doi: {
    icon: 'mdi-file-document-outline',
    hideFacet: true,
  },
  gold_classification: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 0,
  },
  /* GOLD ecosystem type */
  ecosystem: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 1,
    hideFacet: true,
  },
  ecosystem_category: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 2,
    hideFacet: true,
  },
  ecosystem_type: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 3,
    hideFacet: true,
  },
  ecosystem_subtype: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 4,
    hideFacet: true,
  },
  specific_ecosystem: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 5,
    hideFacet: true,
  },
  /* END GOLD ecosystem type */
  /* ENVO terms */
  env_broad_scale: {
    name: 'Environmental biome',
    group: 'ENVO',
    sortKey: 1,
  },
  env_local_scale: {
    name: 'Environmental feature',
    group: 'ENVO',
    sortKey: 2,
  },
  env_medium: {
    name: 'Environmental material',
    group: 'ENVO',
    sortKey: 3,
  },
  open_in_gold: {
    icon: 'mdi-link',
  },
  /* END ENVO terms */
  /* disable uniques */
  scientific_objective: {
    hideFacet: true,
  },
  gold_name: {
    hideFacet: true,
  },
  gold_description: {
    hideFacet: true,
  },
  name: {
    hideFacet: true,
  },
  ncbi_taxonomy_name: {
    hideFacet: true,
  },
  ncbi_project_name: {
    hideFacet: true,
  },
  principal_investigator_image_url: {
    hideFacet: true,
    hideAttr: true,
  },
  /* END disable uniques */
  /* Other non-facet terms to remap */
  reads_qc: {
    name: 'Reads QC',
  },
  mags_analysis: {
    name: 'MAGs analysis',
  },
  nom_analysis: {
    name: 'NOM analysis',
  },
  'Organic Matter Characterization': {
    name: 'Organic Matter',
  },
  multiomics: {
    hideAttr: true,
  },
};

/**
 *  If any of the above overrides should only happen on a single entity,
 * override them here
 */
const tableFields: Record<entityType, Record<string, FieldsData>> = {
  gene_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'KEGG Term',
      description: [
        'KEGG Gene Function search filters results to samples that have at least one of the chosen KEGG terms. '
        + 'Orthology, Pathway, and Module are supported.',
        'Expected format: K00000 or M00000 or MAP00000',
      ],
      encode: keggEncode,
    },
  },
  biosample: {},
  study: {},
  omics_processing: {},
  reads_qc: {},
  metagenome_annotation: {},
  metagenome_assembly: {},
  metaproteomic_analysis: {},
  data_object: {},
};

const ecosystems = [
  {
    name: 'Host-associated',
    color: colors.hostAssociated,
  },
  {
    name: 'Aquatic',
    color: colors.aquatic,
  },
  {
    name: 'Terrestrial',
    color: colors.terrestrial,
  },
  {
    name: 'Engineered',
    color: colors.engineered,
  },
];

function getField(name: string, table?: entityType): FieldsData {
  if (table && table in tableFields) {
    if (name in tableFields[table]) {
      return tableFields[table][name];
    }
  }
  if (name in fields) {
    return fields[name];
  }
  return {};
}

const MultiomicsValue = {
  MB: 0b10000,
  MG: 0b01000,
  MP: 0b00100,
  MT: 0b00010,
  NOM: 0b00001,
};

export {
  types,
  ecosystems,
  MultiomicsValue,
  getField,
  keggEncode,
  stringIsKegg,
};
