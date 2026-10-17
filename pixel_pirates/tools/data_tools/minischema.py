"""Mini-schema validator (Module A5). Python twin of game/core/schema.gd - SAME semantics, proven equal by the shared
fixture file game/tests/fixtures/validator_cases.json (both validators must flag exactly the same error paths).

Schema keys: type (object|array|string|integer|number|boolean), enum, pattern (regex SEARCH, anchor it yourself), min, max,
  props, required, extra (bool, default false = unknown keys are errors), values (schema for keys not in props), key_ref,
  items, min_items, max_items, unique_items, ref (string must exist in lookup kind).
Paths: $ , $.key , $.arr[2]. 'integer' = number without fractional part (Godot parses every JSON number as float).
"""
from __future__ import annotations

import re
from typing import Any, Callable

RefLookup = Callable[[str, str], bool]


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_int(v: Any) -> bool:
    return _is_num(v) and float(v).is_integer()


def _enum_has(options: list, v: Any) -> bool:
    for e in options:
        if _is_num(v) and _is_num(e):
            if v == e:
                return True
        elif type(v) is type(e) and v == e:
            return True
    return False


def validate(value: Any, schema: dict, ref_lookup: RefLookup | None = None) -> list[tuple[str, str]]:
    errs: list[tuple[str, str]] = []
    _check(value, schema, "$", errs, ref_lookup)
    return errs


def error_paths(errs: list[tuple[str, str]]) -> list[str]:
    return sorted({p for p, _ in errs})


def _check(v: Any, s: dict, path: str, errs: list, refs: RefLookup | None) -> None:
    t = s.get("type", "")
    ok = {"object": isinstance(v, dict), "array": isinstance(v, list), "string": isinstance(v, str), "boolean": isinstance(v, bool),
          "number": _is_num(v), "integer": _is_int(v)}.get(t)
    if ok is None:
        errs.append((path, f"schema error: unknown type '{t}'"))
        return
    if not ok:
        errs.append((path, f"expected {t}"))
        return
    if "enum" in s and not _enum_has(s["enum"], v):
        errs.append((path, f"not in enum {s['enum']}"))
    if t == "string":
        if "pattern" in s and re.search(s["pattern"], v) is None:
            errs.append((path, f"does not match {s['pattern']}"))
        if "ref" in s and refs is not None and not refs(s["ref"], v):
            errs.append((path, f"unknown {s['ref']} '{v}'"))
    elif t in ("number", "integer"):
        if "min" in s and v < s["min"]:
            errs.append((path, f"below min {s['min']}"))
        if "max" in s and v > s["max"]:
            errs.append((path, f"above max {s['max']}"))
    elif t == "array":
        if "min_items" in s and len(v) < s["min_items"]:
            errs.append((path, f"fewer than {s['min_items']} items"))
        if "max_items" in s and len(v) > s["max_items"]:
            errs.append((path, f"more than {s['max_items']} items"))
        if s.get("unique_items"):
            for i, x in enumerate(v):
                if x in v[:i]:
                    errs.append((f"{path}[{i}]", "duplicate item"))
        if "items" in s:
            for i, x in enumerate(v):
                _check(x, s["items"], f"{path}[{i}]", errs, refs)
    elif t == "object":
        props = s.get("props", {})
        for k in s.get("required", []):
            if k not in v:
                errs.append((f"{path}.{k}", "required"))
        for k, x in v.items():
            kp = f"{path}.{k}"
            if "key_ref" in s and refs is not None and not refs(s["key_ref"], k):
                errs.append((kp, f"unknown {s['key_ref']} '{k}'"))
            if k in props:
                _check(x, props[k], kp, errs, refs)
            elif "values" in s:
                _check(x, s["values"], kp, errs, refs)
            elif not s.get("extra", False):
                errs.append((kp, "unknown key"))
