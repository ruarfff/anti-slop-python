from anti_slop_python.rules.base import Rule
from anti_slop_python.rules.no_any_containers import RULE as NO_ANY_CONTAINERS
from anti_slop_python.rules.no_dynamic_attribute_access import (
    RULE as NO_DYNAMIC_ATTRIBUTE_ACCESS,
)
from anti_slop_python.rules.too_many_module_lines import RULE as TOO_MANY_MODULE_LINES

RULES: tuple[Rule, ...] = (
    NO_ANY_CONTAINERS,
    NO_DYNAMIC_ATTRIBUTE_ACCESS,
    TOO_MANY_MODULE_LINES,
)

__all__ = ["RULES", "Rule"]
