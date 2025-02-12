from enum import Enum


#: Bitmasks for omics types (see database.update_multiomics_sql)
class MultiomicsValue(Enum):
    mb = 0b100000
    mg = 0b010000
    mp = 0b001000
    mt = 0b000100
    om = 0b000010
    li = 0b000001
