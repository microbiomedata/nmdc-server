from typing import Dict, Optional

from pint import Unit, UnitRegistry

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
