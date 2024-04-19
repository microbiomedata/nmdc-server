<template>
  <v-banner
    color="blue"
    dark
    icon="mdi-information"
    class="ma-4"
  >
    <span
      class="title"
      style="line-height: inherit"
    >
      Announcement:
    </span>
    The NMDC will be replacing legacy identifiers with
    <a href="https://microbiomedata.github.io/nmdc-schema/identifiers/#ids-minted-for-use-within-nmdc">
      NMDC persistent identifiers</a> on April 22, 2024 for studies,
    samples, analysis workflows, and files. Additionally, annotation will be reprocessed for legacy metagenomes
    and metatranscriptomes, along with binning for metagenomes. Legacy metaproteomics datasets will be reprocessed
    using the new metagenome annotations. For information on mapping between old and new identifiers please refer
    to
    <a href="https://microbiomedata.github.io/nmdc-schema/identifiers/#reuse-vs-minting-new-ids">
      this documentation</a>. If you have questions please contact support@microbiomedata.org.
  </v-banner>
</template>
