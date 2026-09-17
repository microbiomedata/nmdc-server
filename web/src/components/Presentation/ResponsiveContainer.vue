<!-- 
 Generalizable responsive container that centers its content
 and constrains its width to a reasonable maximum depending on the screen width.
 -->
<template>
  <v-container
    fluid
  >
    <v-row justify="center">
      <v-col
        md="10"
        lg="8"
        xl="6"
      >
        <slot />
      </v-col>
    </v-row>
  </v-container>
</template>