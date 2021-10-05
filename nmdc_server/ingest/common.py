from datetime import datetime
from typing import Any, Dict, Set, Union

from pydantic import BaseModel

from nmdc_server.schemas import AnnotationValue

JsonValueType = Dict[str, str]
EXCLUDED_FIELDS = {
    "_id",
    # Renamed and duplicated to "alternate_identifiers"
    "alternative_identifiers",
    # Unexpected Study fields
    "relevant_protocols",
    # Unexpected Biosample fields
    "GOLD_sample_identifiers",
    "INSDC_biosample_identifiers",
}


def coerce_value(value: Union[str, int, float]) -> AnnotationValue:
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%d-%b-%y %I.%M.%S.%f000 %p").isoformat()
        except ValueError:
            pass
    return value


def extract_value(value: Any) -> Any:
    # convert {"has_raw_value": <value>} -> <value>
    if isinstance(value, str):
        return value
    elif isinstance(value, dict) and "has_raw_value" in value:
        return coerce_value(value["has_raw_value"])
    return value


def extract_extras(
    cls: BaseModel, values: Dict[str, Any], exclude: Set[str] = None
) -> Dict[str, Any]:
    # Move unknown attributes into values['annotations']
    fields = set(cls.__fields__.keys())
    exclude = (exclude or set()).union(EXCLUDED_FIELDS)
    values.setdefault("annotations", {})
    for key, value in values.items():
        if key not in fields and key not in exclude:
            values["annotations"][key] = extract_value(value)
    return values
