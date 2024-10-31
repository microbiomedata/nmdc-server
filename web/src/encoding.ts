import colors from './colors';
import { entityType, entitySchemaType, KeggTermSearchResponse, api } from './data/api';

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
  group?: string;
  hideAttr?: boolean;
  schemaName?: string; // Match the field to the nmsc schema property
  encode?: (input: string) => string,
}

interface PrefixInfo {
    pattern: RegExp;
    short: Function;
    long: Function;
    urlBase: string;
}

type geneFunctionType = 'kegg' | 'pfam' | 'cog';

interface geneFunctionTypeDescription {
  label: string;
  description: string;
  expectedFormats: string;
  encodeFunction: Function;
  searchFunction: (query: string) => Promise<KeggTermSearchResponse[]>;
}

export const geneFunctionTypeInfo: Record<geneFunctionType, geneFunctionTypeDescription> = {
  kegg: {
    label: '',
    description: '',
    expectedFormats: '',
    encodeFunction: () => undefined,
    searchFunction: api.keggSearch,
  },
  cog: {
    label: '',
    description: '',
    expectedFormats: '',
    encodeFunction: () => undefined,
    searchFunction: api.cogSearch,

  },
  pfam: {
    label: '',
    description: '',
    expectedFormats: '',
    encodeFunction: () => undefined,
    searchFunction: api.pfamSearch,
  },
};

const pathwayRegex = /^((map:?)|(path:?)|(ko:?)|(ec:?)|(rn:?)|(kegg.pathway:(map|path|ec|ko|rn)))(?=\d{5})/i;

function pathwayPrefixShort(v: string) {
  const match = v.match(pathwayRegex);
  if (match) {
    const prefix = match[8] ? match[8] : match[1].replace(/:$/, '');
    return prefix.toLowerCase();
  }
  return 'map';
}

function pathwayPrefixLong(v: string) {
  const match = v.match(pathwayRegex);
  if (match) {
    const prefix = match[7] ? match[7] : match[1].replace(match[1], `kegg.pathway:${match[1]}`);
    return prefix.toUpperCase();
  }
  return 'KEGG.PATHWAY.MAP';
}

const KeggPrefix: Record<string, PrefixInfo> = {
  ORTHOLOGY: {
    pattern: /^((k:?)|(kegg\.orthology:k))(?=\d{5})/i,
    short: () => 'k',
    long: () => 'KEGG.ORTHOLOGY:K',
    urlBase: 'https://www.genome.jp/entry/',
  },
  PATHWAY: {
    pattern: pathwayRegex,
    short: pathwayPrefixShort,
    long: pathwayPrefixLong,
    urlBase: 'https://www.genome.jp/kegg-bin/show_pathway?',
  },
  MODULE: {
    pattern: /^((m:?)|(kegg.module:m))(?=\d{5})/i,
    short: () => 'M',
    long: () => 'KEGG.MODULE:M',
    urlBase: 'https://www.kegg.jp/entry/',
  },
};

/**
 * Encode a string as either the long or short variant of
 * a KEGG identifier term.
 */
function keggEncode(v: string, url = false) {
  const prefixes = Object.values(KeggPrefix);
  for (let i = 0; i < prefixes.length; i += 1) {
    const {
      pattern, short, long, urlBase,
    } = prefixes[i];
    const replacement = url ? short(v) : long(v);
    const transformed = v.replace(pattern, replacement);
    if (transformed !== v) {
      if (url) {
        return urlBase + transformed;
      }
      return transformed;
    }
  }
  return v;
}

function stringIsKegg(v: string) {
  return Object.values(KeggPrefix).find((item) => v.match(item.pattern));
}

function makeSetsFromBitmask(mask_str: string) {
  const mask = parseInt(mask_str, 10); // the bitmask comes in as a string
  const sets = [];

  /* eslint-disable no-bitwise */
  if (1 & mask) {
    sets.push('NOM');
  }
  if ((1 << 4) & mask) {
    sets.push('MB');
  }
  if ((1 << 2) & mask) {
    sets.push('MP');
  }
  if ((1 << 1) & mask) {
    sets.push('MT');
  }
  if ((1 << 3) & mask) {
    sets.push('MG');
  }
  return sets;
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
    heading: 'Data Types',
    name: 'omics_processing',
    plural: 'Data Generations',
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
  kegg_function: {
    icon: 'mdi-dna',
    heading: 'Gene Function',
    name: 'gene_function',
    plural: 'Gene functions',
    visible: true,
  },
  pfam_function: {
    icon: 'mdi-dna',
    heading: 'Gene Function',
    name: 'gene_function',
    plural: 'Gene functions',
    visible: true,
  },
  cog_function: {
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
  kegg: {
    icon: 'mdi-key',
    hideFacet: true,
  },
  pfam: {
    icon: 'mdi-key',
    hideFacet: true,
  },
  cog: {
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
    name: 'Collection Date',
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
    name: 'GOLD Classification',
    group: 'GOLD Ecosystems',
    sortKey: 0,
  },
  instrument_name: {
    name: 'Instrument Name',
    group: 'Data Generation',
  },
  omics_type: {
    name: 'Data Type',
    group: 'Data Generation',
  },
  processing_institution: {
    name: 'Processing Institution',
    group: 'Data Generation',
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
  /* MIxS Environmental Triad terms */
  env_broad_scale: {
    name: 'Broad-scale Environmental Context',
    group: 'MIxS Environmental Triad',
    sortKey: 1,
  },
  env_local_scale: {
    name: 'Local Environmental Context',
    group: 'MIxS Environmental Triad',
    sortKey: 2,
  },
  env_medium: {
    name: 'Environmental Medium',
    group: 'MIxS Environmental Triad',
    sortKey: 3,
  },
  open_in_gold: {
    icon: 'mdi-link',
  },
  /* END MIxS Environmental Triad terms */
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
  image_url: {
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
    name: 'Natural Organic Matter',
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
  kegg_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'KEGG',
      encode: keggEncode,
    },
  },
  cog_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'PFAM',
    },
  },
  pfam_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'COG',
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
  makeSetsFromBitmask,
};
