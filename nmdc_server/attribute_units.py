from typing import Dict, Optional

from pint import Quantity, UnitRegistry
from pint.facets.plain.unit import PlainUnit

_registry = UnitRegistry()

# TODO: This information should come from the upstream schema.  For now, we
#       hard code relevant attributes here.


_unit_info: Dict[str, Dict[str, PlainUnit]] = {
    "biosample": {
        "depth": _registry("meter").units,
    }
}


def get_attribute_units(table: str, attribute: str) -> Optional[PlainUnit]:
    return _unit_info.get(table, {}).get(attribute)


def extract_quantity(obj: dict, table: str, attribute: str, value_field: str = "has_numeric_value", ) -> Optional[float]:
    """Extract units from https://microbiomedata.github.io/nmdc-schema/QuantityValue/"""
    expected_units = get_attribute_units(table, attribute)
    value = obj.get(value_field, None)
    units = obj.get("has_unit", None)
    if value is None:
        return None
    if units is None:
        return value
    quantity: Quantity = _registry(units).units * value
    return quantity.to(expected_units).magnitude
