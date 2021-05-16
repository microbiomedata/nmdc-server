from enum import Enum


class MultiomicsValue(Enum):
    mb = 0b10000
    mg = 0b01000
    mp = 0b00100
    mt = 0b00010
    om = 0b00001
