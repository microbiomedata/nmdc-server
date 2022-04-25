from typing import Dict, Optional

from pint import Quantity, Unit, UnitRegistry

_registry = UnitRegistry()

# TODO: This information should come from the upstream schema.  For now, we
#       hard code relevant attributes here.


_unit_info: Dict[str, Dict[str, Unit]] = {
    "biosample": {
        "depth": _registry("meter").units,
    }
}


def get_attribute_units(table: str, attribute: str) -> Optional[Unit]:
    return _unit_info.get(table, {}).get(attribute)


def extract_quantity(obj: dict, table: str, attribute: str) -> Optional[float]:
    """Extract units from https://microbiomedata.github.io/nmdc-schema/QuantityValue/"""
    expected_units = get_attribute_units(table, attribute)
    value = obj.get("has_numeric_value", None)
    units = obj.get("has_unit", None)
    if value is None:
        return None
    if units is None:
        return value
    quantity: Quantity = _registry(units).units * value
    return quantity.to(expected_units).magnitude
