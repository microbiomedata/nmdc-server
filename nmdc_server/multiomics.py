from enum import Enum


#: Bitmasks for omics types (see database.update_multiomics_sql)
class MultiomicsValue(Enum):
    mb = 0b1000000
    mg = 0b0100000
    mp = 0b0010000
    mt = 0b0001000
    om = 0b0000100
    li = 0b0000010
    am = 0b0000001
