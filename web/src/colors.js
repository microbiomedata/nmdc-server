import colors from 'vuetify/lib/util/colors';

const red = '#ED5338';
const red2 = '#ff5252'
const orange = '#E88320';
const orangeLight = '#EEA359';
const orangeLighter = '#EEC295';
const green = colors.lightGreen.darken2;
const blue = '#00AAE7';
const blueLight = '#5CD3FF';
const blueDark = '#0087B8';
const blueDarker = '#004B66';
const purple = '#4F3B80';
const purpleLight = '#7D6FA1';
const purpleLightest = colors.purple.lighten4;

export default {
  red,
  orange,
  orangeLight,
  orangeLighter,
  green,
  blue,
  blueDark,
  blueDarker,
  purple,
  purpleLightest,
  grey: colors.grey,
  primary: purple,
  secondary: red,
  info: blue,
  accent: orange,
  link: purple,
  visited: purpleLight,
  visualization: blue,
  visualizationLight: blueLight,
  aquatic: blue,
  terrestrial: green,
  hostAssociated: red,
  engineered: orange,
  metagenome: blue,
  metatranscriptome: green,
  sequencing: red,
  success: green,
  error: red2,
};
