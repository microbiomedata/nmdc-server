import colors from './colors';

const types = {
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
    icon: 'mdi-earth',
    heading: 'Environments',
    name: 'sample',
    plural: 'samples',
    visible: true,
  },
  reads_qc: {
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
};

const fields = {
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
  /* GOLD ecosystem type */
  ecosystem: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 1,
  },
  ecosystem_category: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 2,
  },
  ecosystem_type: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 3,
  },
  ecosystem_subtype: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 4,
  },
  specific_ecosystem: {
    icon: 'mdi-pine-tree',
    group: 'GOLD Ecosystems',
    sortKey: 5,
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

const omicsTypes = {
  Metagenome: {
    color: colors.blue,
  },
  Metatranscriptome: {
    color: colors.blue,
  },
  'Whole Genome Sequencing': {
    color: colors.blue,
  },
  Proteomics: {
    color: colors.blue,
  },
  Metabolomics: {
    color: colors.blue,
  },
  Lipidomics: {
    color: colors.blue,
  },
  'Organic Matter Characterization': {
    color: colors.blue,
  },
};

const values = {
  Metagenome: {
    color: colors.primary,
  },
  Metatranscriptome: {
    color: colors.primary,
  },
  'Whole Genome Sequencing': {
    color: colors.primary,
  },
  Proteomics: {
    color: colors.primary,
  },
  Metabolomics: {
    color: colors.primary,
  },
  Lipidomics: {
    color: colors.primary,
  },
  'Organic Matter Characterization': {
    color: colors.primary,
  },
  Environmental: {
    color: colors.terrestrial,
  },
  Terrestrial: {
    color: colors.terrestrial,
  },
  Soil: {
    color: colors.terrestrial,
  },
  'Deep subsurface': {
    color: colors.terrestrial,
  },
  Sand: {
    color: colors.terrestrial,
  },
  Wetlands: {
    color: colors.terrestrial,
  },
  'Fracking water': {
    color: colors.terrestrial,
  },
  'Forest Soil': {
    color: colors.terrestrial,
  },
  Permafrost: {
    color: colors.terrestrial,
  },
  'Host-associated': {
    color: colors.hostAssociated,
  },
  Plants: {
    color: colors.hostAssociated,
  },
  Microbial: {
    color: colors.hostAssociated,
  },
  Bacteria: {
    color: colors.hostAssociated,
  },
  Rhizosphere: {
    color: colors.hostAssociated,
  },
  Phylloplane: {
    color: colors.hostAssociated,
  },
  Epiphytes: {
    color: colors.hostAssociated,
  },
  Aquatic: {
    color: colors.aquatic,
  },
  Marine: {
    color: colors.aquatic,
  },
  'Cold seeps': {
    color: colors.aquatic,
  },
  Sediment: {
    color: colors.aquatic,
  },
  'Intertidal zone': {
    color: colors.aquatic,
  },
  'Salt marsh': {
    color: colors.aquatic,
  },
  Engineered: {
    color: colors.engineered,
  },
  'Lab enrichment': {
    color: colors.engineered,
  },
  'Defined media': {
    color: colors.engineered,
  },
};

const ecosystemCategory = {
  Bioreactor: {
    icon: 'test-tube-empty',
    color: 'green',
  },
  Bioremediation: {
    icon: 'waves',
    color: 'black',
  },
  Biotransformation: {
    icon: 'molecule',
    color: 'pink',
  },
  'Built environment': {
    icon: 'domain',
    color: 'green',
  },
  'Food production': {
    icon: 'food-apple',
    color: 'red',
  },
  'Industrial production': {
    icon: 'factory',
    color: 'grey',
  },
  'Lab enrichment': {
    icon: 'test-tube-empty',
    color: 'grey',
  },
  'Lab synthesis': {
    icon: 'flask-round-bottom',
    color: 'blue',
  },
  'Laboratory developed': {
    icon: 'flask-outline',
    color: 'blue',
  },
  Modeled: {
    icon: 'code-braces-box',
    color: 'blue-grey',
  },
  Paper: {
    icon: 'file-outline',
    color: 'black',
  },
  'Solid waste': {
    icon: 'trash-can',
    color: 'grey',
  },
  Unclassified: {
    icon: 'help-rhombus-outline',
    color: 'grey',
  },
  WWTP: {
    icon: 'air-filter',
    color: 'cyan',
  },
  Wastewater: {
    icon: 'waves',
    color: 'brown',
  },
  Air: {
    icon: 'weather-windy',
    color: 'light-blue',
  },
  Aquatic: {
    icon: 'waves',
    color: 'blue',
  },
  Terrestrial: {
    icon: 'shovel',
    color: 'brown',
  },
  Algae: {
    icon: 'waves',
    color: 'green',
  },
  Amphibia: {
    icon: 'bug',
    color: 'green',
  },
  Animal: {
    icon: 'dog',
    color: 'brown',
  },
  Annelida: {
    icon: 'bug',
    color: 'grey',
  },
  Arthropoda: {
    icon: 'spider',
    color: 'black',
  },
  Birds: {
    icon: 'twitter',
    color: 'yellow',
  },
  Cnidaria: {
    icon: 'jellyfish',
    color: 'pink',
  },
  Echinodermata: {
    icon: 'star',
    color: 'deep-orange',
  },
  Endosymbionts: {
    icon: 'bee',
    color: 'amber',
  },
  Fish: {
    icon: 'fish',
    color: 'cyan',
  },
  Fungi: {
    icon: 'mushroom',
    color: 'deep-orange',
  },
  Horse: {
    icon: 'horseshoe',
    color: 'brown',
  },
  Human: {
    icon: 'human',
    color: 'grey',
  },
  Insecta: {
    icon: 'bee',
    color: 'black',
  },
  Invertebrates: {
    icon: 'bug',
    color: 'grey',
  },
  Mammals: {
    icon: 'dog-side',
    color: 'brown',
  },
  Microbial: {
    icon: 'bug-outline',
    color: 'green',
  },
  Mollusca: {
    icon: 'octagram',
    color: 'purple',
  },
  Plants: {
    icon: 'sprout',
    color: 'green',
  },
  Porifera: {
    icon: 'waves',
    color: 'deep-orange',
  },
  Protists: {
    icon: 'bug-outline',
    color: 'lime',
  },
  Protozoa: {
    icon: 'bug-outline',
    color: 'teal',
  },
  Reptilia: {
    icon: 'turtle',
    color: 'green',
  },
  Tunicates: {
    icon: 'water',
    color: 'indigo',
  },
};

const tables = [
  'study',
  'biosample',
  'project',
];

const ecosystemFields = [
  'ecosystem',
  'ecosystem_category',
  'ecosystem_type',
  'ecosystem_subtype',
  'specific_ecosystem',
];

function getField(name) {
  if (name in fields) {
    return fields[name];
  }
  return null;
}

export {
  types,
  tables,
  fields,
  ecosystems,
  omicsTypes,
  values,
  ecosystemCategory,
  ecosystemFields,
  getField,
};
