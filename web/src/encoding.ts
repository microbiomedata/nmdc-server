import colors from './colors';
import { entityType } from './data/api';

export interface EntityData {
  icon: string;
  heading: string;
  name: string;
  plural: string;
  visible: boolean;
}

export interface FieldsData {
  icon?: string;
  hideFacet?: boolean;
  sortKey?: number;
  name?: string;
  group?: string;
  hideAttr?: boolean;
  encode?: (input: string) => string,
}

const types: Record<entityType, EntityData> = {
  study: {
    icon: 'mdi-book',
    heading: 'Studies',
    name: 'study',
    plural: 'studies',
    visible: true,
  },
  project: {
    icon: 'mdi-file-table-box-multiple-outline',
    heading: 'Omics Types',
    name: 'project',
    plural: 'projects',
    visible: true,
  },
  biosample: {
    icon: 'mdi-test-tube',
    heading: 'Environments',
    name: 'sample',
    plural: 'samples',
    visible: true,
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
  },
  metagenome_annotation: {
    icon: 'mdi-dna',
    heading: 'Metagenome Annotation',
    name: 'metagenome_annotation',
    plural: 'Metagenome annotation',
    visible: true,
  },
  metaproteomic_analysis: {
    icon: 'mdi-dna',
    heading: 'Metaproteomic Analysis',
    name: 'metaproteomic_analysis',
    plural: 'Metaproteomic analysis',
    visible: true,
  },
  data_object: {
    icon: 'mdi-database',
    heading: 'Data Object',
    name: 'data_object',
    plural: 'Data objects',
    visible: false,
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
  project_id: {
    icon: 'mdi-key-link',
    hideFacet: true,
  },
  git_url: {
    icon: 'mdi-git',
    hideFacet: true,
  },
  location: {
    icon: 'mdi-earth',
  },
  latitude: {
    icon: 'mdi-earth',
    hideFacet: false,
  },
  longitude: {
    icon: 'mdi-earth',
    hideFacet: false,
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
  sample_collection_site: {
    icon: 'mdi-earth',
  },
  geographic_location: {
    icon: 'mdi-earth',
  },
  add_date: {
    icon: 'mdi-calendar',
    hideFacet: true,
  },
  mod_date: {
    icon: 'mdi-calendar',
    hideFacet: true,
  },
  ecosystem_path_id: {
    icon: 'mdi-pine-tree',
    hideFacet: true,
  },
  habitat: {
    icon: 'mdi-pine-tree',
  },
  community: {
    icon: 'mdi-google-circles-communities',
  },
  principal_investigator_name: {
    icon: 'mdi-account',
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
  ncbi_project_name: {
    hideFacet: true,
  },
  principal_investigator_image_url: {
    hideFacet: true,
    hideAttr: true,
  },
  /* END disable uniques */
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
      name: 'KO term',
      encode: (v: string) => {
        const prefix = 'KEGG:ORTHOLOG';
        if (v.startsWith(prefix)) return v;
        return `${prefix}:${v}`;
      },
    },
  },
  biosample: {},
  study: {},
  project: {},
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

export {
  types,
  ecosystems,
  getField,
};
