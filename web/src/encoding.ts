// @ts-ignore
import colors from './colors';
import {
  entityType, entitySchemaType, KeggTermSearchResponse, api,
} from './data/api';

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

type geneFunctionType = 'kegg' | 'pfam' | 'cog' | 'go';

export const geneFunctionTables = ['kegg_function', 'pfam_function', 'cog_function', 'go_function'];

const pathwayRegex = /^((map:?)|(path:?)|(ko:?)|(ec:?)|(rn:?)|(kegg.pathway:(map|path|ec|ko|rn)))(?=\d{5})/i;

function pathwayPrefixShort(v: string) {
  const match = v.match(pathwayRegex);
  if (match) {
    const prefix = match[8] ? match[8] : match[1]?.replace(/:$/, '');
    return prefix?.toLowerCase();
  }
  return 'map';
}

function pathwayPrefixLong(v: string) {
  const match = v.match(pathwayRegex);
  if (match) {
    const prefix = match[7] ? match[7] : match[1]?.replace(match[1], `kegg.pathway:${match[1]}`);
    return prefix?.toUpperCase();
  }
  return 'KEGG.PATHWAY.MAP';
}

const KeggPrefix: Record<string, PrefixInfo> = {
  ORTHOLOGY: {
    pattern: /^((k:?)|(kegg\.orthology:k))(?=\d{5})/i,
    short: () => 'k',
    long: () => 'KEGG.ORTHOLOGY:K',
    urlBase: 'https://bioregistry.io/kegg.orthology:/',
  },
  PATHWAY: {
    pattern: pathwayRegex,
    short: pathwayPrefixShort,
    long: pathwayPrefixLong,
    urlBase: 'https://bioregistry.io/kegg.pathway:/',
  },
  MODULE: {
    pattern: /^((m:?)|(kegg.module:m))(?=\d{5})/i,
    short: () => 'M',
    long: () => 'KEGG.MODULE:M',
    urlBase: 'https://bioregistry.io/kegg.module:/',
  },
};

/**
 * Encode a string as either the long or short variant of
 * a KEGG identifier term.
 */
function keggEncode(v: string, url = false) {
  const prefixes = Object.values(KeggPrefix);
  for (let i = 0; i < prefixes.length; i += 1) {
    const prefix = prefixes[i];
    if (!prefix) continue;
    const {
      pattern, short, long, urlBase,
    } = prefix;
    const replacement = url ? short(v) : long(v);
    const transformed = v.replace(pattern, replacement);
    if (transformed !== v) {
      if (url) {
        return urlBase + transformed.toUpperCase();
      }
      return transformed;
    }
  }
  return v;
}

function cogEncode(v: string, url = false) {
  // COG terms, pathways and functions don't need to be transformed
  // So either just return it with a prefix so our backend can process it.
  if (!url) {
    // COG categories are just identified by a single letter
    if (v.length === 1) {
      return `COG.FUNCTION:${v}`;
    }
    // COGs themselves start with this prefix
    if (v.startsWith('COG')) {
      return `COG:${v}`;
    }
    // Pathways are identified by a name. If the other two conditions have not
    // been met at this point, assume it is a pathway.
    return `COG.PATHWAY:${v}`;
  }
  // Or figure out if it is a term, pathway, or function
  const urlBase = 'https://bioregistry.io/cog';
  const id = v.split(':')[1];
  if (v.length === 1 || v.startsWith('COG.FUNCTION:')) {
    return `${urlBase}.category:/${id}`;
  }
  if (v.startsWith('COG.PATHWAY')) {
    return `${urlBase}.pathway:/${id}`;
  }
  if (v.startsWith('COG:COG')) {
    return `${urlBase}:/${id}`;
  }
  return v;
}

function pfamEncode(v: string, url = false) {
  if (!url) {
    if (v.startsWith('PF')) {
      return `PFAM:${v}`;
    }
    return `PFAM.CLAN:${v}`;
  }
  const urlBase = 'https://bioregistry.io/pfam';
  const id = v.split(':')[1];
  if (v.includes('CLAN')) {
    return `${urlBase}.clan:/${id}`;
  }
  return `${urlBase}:/${id}`;
}

function goEncode(v: string, url = false) {
  if (url) {
    return `https://bioregistry.io/go:/${v.split(':')[1]}`;
  }
  return v;
}

export interface GeneFunctionSearchParams {
  description: string;
  label: string;
  expectedFormats: string;
  helpSite: string;
  table: entityType;
  encodeFunction: (value: string, url: boolean) => string;
  searchFunction: (query: string) => Promise<KeggTermSearchResponse[]>;
  searchWithInputText: (value: string) => boolean;
}

function stringIsKegg(v: string) {
  return !!Object.values(KeggPrefix).find((item) => v.match(item.pattern));
}

export const geneFunctionTypeInfo: Record<geneFunctionType, GeneFunctionSearchParams> = {
  kegg: {
    label: 'KEGG',
    description: `
      KEGG Gene Function search filters results to
      samples that have at least one of the chosen KEGG terms.
      Orthology, Module, and Pathway are supported.
    `,
    expectedFormats: 'K00000, M00000, map00000, ko00000, rn00000, and ec00000',
    helpSite: 'https://www.genome.jp/kegg/',
    table: 'kegg_function',
    encodeFunction: keggEncode,
    searchFunction: api.keggSearch,
    searchWithInputText: stringIsKegg,
  },
  cog: {
    label: 'COG',
    description: `
      COG Gene Function search filters results to
      samples that have at least one of the chosen COG terms.
      Term, Function, and Pathway are supported.
    `,
    expectedFormats: 'COG0000',
    helpSite: 'https://www.ncbi.nlm.nih.gov/research/cog/',
    table: 'cog_function',
    encodeFunction: cogEncode,
    searchFunction: api.cogSearch,
    searchWithInputText: () => false,

  },
  pfam: {
    label: 'PFAM',
    description: `
      Pfam Gene Function search filters results to
      samples that have at least one of the chosen Pfam terms.
      Entry and Clan are supported.
    `,
    expectedFormats: 'PF00000, CL0000',
    helpSite: 'https://www.ebi.ac.uk/interpro/set/all/entry/pfam/',
    table: 'pfam_function',
    encodeFunction: pfamEncode,
    searchFunction: api.pfamSearch,
    searchWithInputText: () => false,
  },
  go: {
    label: 'GO',
    description: `
      GO gene function search filters result to samples that match
      at least one of the chosen GO terms.
    `,
    expectedFormats: 'GO:0000000',
    helpSite: 'https://www.geneontology.org/',
    table: 'go_function',
    encodeFunction: goEncode,
    searchFunction: api.goSearch,
    searchWithInputText: () => false,
  },
};

function makeSetsFromBitmask(mask_str: string) {
  const mask = parseInt(mask_str, 10); // the bitmask comes in as a string
  const sets = [];

  /* eslint-disable no-bitwise */
  if ((1 << 2) & mask) {
    sets.push('NOM');
  }
  if ((1 << 6) & mask) {
    sets.push('MB');
  }
  if ((1 << 4) & mask) {
    sets.push('MP');
  }
  if ((1 << 3) & mask) {
    sets.push('MT');
  }
  if ((1 << 5) & mask) {
    sets.push('MG');
  }
  if ((1 << 1) & mask) {
    sets.push('LIP');
  }
  if (1 & mask) {
    sets.push('AMP');
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
  go_function: {
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
    icon: 'mdi-link',
    name: 'Broad-scale Environmental Context',
    group: 'MIxS Environmental Triad',
    sortKey: 1,
  },
  env_local_scale: {
    icon: 'mdi-link',
    name: 'Local Environmental Context',
    group: 'MIxS Environmental Triad',
    sortKey: 2,
  },
  env_medium: {
    icon: 'mdi-link',
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
      name: 'COG',
      encode: cogEncode,
    },
  },
  pfam_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'PFAM',
      encode: pfamEncode,
    },
  },
  go_function: {
    id: {
      icon: 'mdi-dna',
      group: 'Function',
      name: 'GO',
      encode: goEncode,
    },
  },
  biosample: {},
  study: {},
  omics_processing: {
    mass_spectrometry_configuration_name: {
      name: 'Mass Spectrometry Method',
      schemaName: 'MassSpectrometryConfiguration',
    },
    chromatography_configuration_name: {
      name: 'Chromatography Method',
      schemaName: 'ChromatographyConfiguration',
    },
    instrument_name: {
      name: 'Instrument Name',
      group: 'Data Generation',
      schemaName: 'Instrument',
    },
    omics_type: {
      name: 'Data Type',
      group: 'Data Generation',
      schemaName: 'analyte_category',
    },
  },
  reads_qc: {},
  metagenome_annotation: {},
  metagenome_assembly: {},
  metaproteomic_analysis: {
    metaproteomics_analysis_category: {
      name: 'Metaproteomics Analysis Category',
      schemaName: 'metaproteomics_analysis_category',
    },
  },
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
      return tableFields[table][name]!;
    }
  }
  if (name in fields) {
    return fields[name]!;
  }
  return {};
}

const MultiomicsValue = {
  MB: 0b1000000,
  MG: 0b0100000,
  MP: 0b0010000,
  MT: 0b0001000,
  NOM: 0b0000100,
  LIP: 0b0000010,
  AMP: 0b0000001,
};

const metaproteomicCategoryEnumToDisplay = {
  matched_metagenome: 'NMDC metagenome matched',
  in_silico_metagenome: 'Uniprot reference genome matched',
};

export {
  types,
  geneFunctionType,
  ecosystems,
  MultiomicsValue,
  getField,
  keggEncode,
  cogEncode,
  pfamEncode,
  stringIsKegg,
  makeSetsFromBitmask,
  metaproteomicCategoryEnumToDisplay,
};
