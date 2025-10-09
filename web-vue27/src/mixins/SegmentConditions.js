export default {
  computed: {
    otherConditions() {
      // conditions from OTHER fields
      return this.conditions.filter((c) => (c.field !== this.field) || (c.table !== this.table));
    },
    myConditions() {
      // conditions that match our field.
      return this.conditions.filter((c) => (c.field === this.field) && (c.table === this.table));
    },
  },
};
