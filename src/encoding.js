import colors from './colors';

export const types = {
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
  sample: {
    icon: 'mdi-earth',
    heading: 'Habitats',
    name: 'sample',
    plural: 'samples',
    visible: true,
  },
  data_object: {
    icon: 'mdi-file-table-outline',
    heading: 'Data Types',
    name: 'data object',
    plural: 'data objects',
    visible: false,
  },
};

export const fields = {
  location: {
    icon: 'mdi-earth',
  },
  latitude: {
    icon: 'mdi-earth',
  },
  longitude: {
    icon: 'mdi-earth',
  },
  sample_collection_site: {
    icon: 'mdi-earth',
  },
  geographic_location: {
    icon: 'mdi-earth',
  },
  add_date: {
    icon: 'mdi-calendar',
    hide: true,
  },
  mod_date: {
    icon: 'mdi-calendar',
    hide: true,
  },
  ecosystem: {
    icon: 'mdi-pine-tree',
    hide: true,
  },
  ecosystem_category: {
    icon: 'mdi-pine-tree',
    hide: true,
  },
  ecosystem_type: {
    icon: 'mdi-pine-tree',
    hide: true,
  },
  ecosystem_subtype: {
    icon: 'mdi-pine-tree',
    hide: true,
  },
  specific_ecosystem: {
    icon: 'mdi-pine-tree',
    hide: true,
  },
  ecosystem_path_id: {
    icon: 'mdi-pine-tree',
    hide: true,
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
    hide: true,
  },
};

export const ecosystems = [
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

// eslint-disable-next-line camelcase
export const ecosystem_category = {
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
