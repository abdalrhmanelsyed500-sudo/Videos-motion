"""Static type-consistency scan of the GDScript project (a heuristic stand-in for part of Godot's parser; NOT Godot).

  python tools/h2d/check_gd_types.py [--all]

Why it exists: H2D-1.2 shipped with `cay_world.build(vp: Node3D, ...)` called with a SubViewport, which Godot's analyzer rejects
as a Parser Error and gdparse / gdlint cannot see. This script reads every .gd file, builds a table of the project classes
(`const X := preload("res://...gd")` aliases, member vars, consts, funcs with typed parameters and return types) and checks:

  1. call arguments whose static type is known against the declared parameter type (class hierarchy aware, including a table of
     the Godot node classes this project uses)           -> "argument N should be A but is B"
  2. calls and member reads on a project class that does not define them                 -> "no method / member"
  3. wrong argument count on project functions
  4. `var x := <expr>` whose right side is a Variant (a Dictionary / untyped Array subscript or `.get()`)   -> parse error in Godot
  5. `var x: T = <expr>` and `return <expr>` whose static type is known and incompatible with T / the declared return type

Types are only inferred for simple forms (literals, constructors, typed vars, typed params, casts, project calls); anything else
is "unknown" and never reported, so a clean run is NOT proof. By default only files changed by H2D-1.2 are scanned; --all scans
every file.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "game"
H12_FILES = {"h2d/h2d0.gd", "h2d/sea_view_3d.gd", "h2d/cay_world.gd", "h2d/cay_scatter.gd", "h2d/land_walker.gd",
             "tests/test_land.gd", "tests/test_scatter.gd", "tests/test_harbor.gd", "h2d/sea_view.gd", "h2d/sea_view_2d.gd"}

PARENT = {
    "SubViewport": "Viewport", "Viewport": "Node", "Node3D": "Node", "Node2D": "CanvasItem", "CanvasItem": "Node",
    "Control": "CanvasItem", "CanvasLayer": "Node", "RefCounted": "Object", "Node": "Object", "Resource": "RefCounted",
    "VisualInstance3D": "Node3D", "GeometryInstance3D": "VisualInstance3D", "MeshInstance3D": "GeometryInstance3D",
    "MultiMeshInstance3D": "GeometryInstance3D", "Camera3D": "Node3D", "Light3D": "VisualInstance3D",
    "DirectionalLight3D": "Light3D", "OmniLight3D": "Light3D", "WorldEnvironment": "Node", "Label": "Control",
    "TextureRect": "Control", "ColorRect": "Control", "Sprite2D": "Node2D", "SceneTree": "Object", "Timer": "Node",
    "Texture2D": "Texture", "Texture": "Resource", "ImageTexture": "Texture2D", "CompressedTexture2D": "Texture2D",
    "Material": "Resource", "ShaderMaterial": "Material", "StandardMaterial3D": "Material", "Mesh": "Resource",
    "QuadMesh": "Mesh", "PlaneMesh": "Mesh", "BoxMesh": "Mesh", "MultiMesh": "Resource", "Shader": "Resource",
    "Image": "Resource", "Object": "",
}
SCALARS = {"int", "float", "bool", "String", "StringName", "Vector2", "Vector2i", "Vector3", "Vector3i", "Vector4", "Color",
           "Rect2", "AABB", "Transform3D", "Basis", "Array", "Dictionary", "Callable", "PackedFloat32Array",
           "PackedByteArray", "PackedStringArray", "PackedVector2Array", "NodePath", "Transform2D"}
OBJECT_METHODS = {"new", "free", "queue_free", "call", "callv", "get", "set", "has_method", "connect", "emit_signal", "get_class",
                  "is_class", "to_string", "duplicate", "get_script", "add_child", "get_tree", "name"}
CONV = {"int": "int", "float": "float", "str": "String", "absf": "float", "maxf": "float", "minf": "float", "clampf": "float",
        "sqrt": "float", "floorf": "float", "roundf": "float", "lerpf": "float", "sinf": "float", "cosf": "float",
        "absi": "int", "maxi": "int", "mini": "int", "clampi": "int", "floori": "int", "roundi": "int", "randf": "float",
        "fposmod": "float", "pow": "float", "deg_to_rad": "float", "rad_to_deg": "float", "bool": "bool", "atan2": "float"}
errors: list[str] = []


@dataclass
class Func:
    name: str
    params: list[tuple[str, str | None, bool]]    # name, type, has_default
    ret: str | None
    line: int


@dataclass
class Cls:
    path: str
    extends: str = ""
    vars: dict[str, str | None] = field(default_factory=dict)
    consts: dict[str, str | None] = field(default_factory=dict)
    funcs: dict[str, Func] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)    # const Alias := preload(path) -> path
    inner: set[str] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    nos: list[int] = field(default_factory=list)


def split_top(s: str, sep: str = ",") -> list[str]:
    out, depth, cur, q = [], 0, "", ""
    i = 0
    while i < len(s):
        c = s[i]
        if q:
            cur += c
            if c == "\\":
                cur += s[i + 1] if i + 1 < len(s) else ""
                i += 1
            elif c == q:
                q = ""
        elif c in "\"'":
            q = c
            cur += c
        elif c in "([{":
            depth += 1
            cur += c
        elif c in ")]}":
            depth -= 1
            cur += c
        elif c == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += c
        i += 1
    if cur.strip() or out:
        out.append(cur)
    return [x.strip() for x in out]


def strip_comment(line: str) -> str:
    q = ""
    for i, c in enumerate(line):
        if q:
            if c == q and line[i - 1] != "\\":
                q = ""
        elif c in "\"'":
            q = c
        elif c == "#":
            return line[:i].rstrip()
    return line.rstrip()


def load_classes() -> dict[str, Cls]:
    classes: dict[str, Cls] = {}
    for f in sorted(GAME.rglob("*.gd")):
        rel = f.relative_to(GAME).as_posix()
        c = Cls(path="res://" + rel)
        raw = f.read_text().splitlines()
        # join continuation lines inside brackets so signatures spanning lines parse
        lines, buf, depth, nos, first = [], "", 0, [], 0
        for k, ln in enumerate(raw, 1):
            code = strip_comment(ln)
            if not buf:
                first = k
            buf = (buf + " " + code.strip()) if buf else code
            depth += sum(code.count(x) for x in "([{") - sum(code.count(x) for x in ")]}")
            if depth <= 0:
                lines.append(buf)
                nos.append(first)
                buf, depth = "", 0
        c.lines = lines
        c.nos = nos
        for no, ln in enumerate(lines, 1):
            if not ln or ln[0] in " \t":
                continue
            m = re.match(r'extends\s+(?:"([^"]+)"|(\w+))', ln)
            if m:
                c.extends = m.group(1) or m.group(2)
            m = re.match(r"class\s+(\w+)", ln)
            if m:
                c.inner.add(m.group(1))
            m = re.match(r'const\s+(\w+)\s*:?=\s*preload\("([^"]+)"\)', ln)
            if m:
                c.aliases[m.group(1)] = m.group(2)
                continue
            m = re.match(r"const\s+(\w+)\s*(?::\s*([\w\[\]]+))?\s*(:?=)\s*(.*)", ln)
            if m:
                c.consts[m.group(1)] = m.group(2) or ty(m.group(4), c, {}, classes)
                continue
            m = re.match(r"(?:@\w+(?:\([^)]*\))?\s+)*var\s+(\w+)\s*(?::\s*([\w\[\]\.]+))?\s*(:?=\s*(.*))?", ln)
            if m:
                t = m.group(2)
                if not t and m.group(4) and ln.split("=")[0].rstrip().endswith(":"):
                    t = ty(m.group(4), c, {}, classes)
                c.vars[m.group(1)] = t
                continue
            m = re.match(r"enum\s*(\w*)\s*\{", ln)
            if m:
                c.consts[m.group(1) or "_enum"] = "int"
                for item in re.findall(r"(\w+)\s*(?:=[^,}]*)?[,}]", ln.split("{", 1)[1]):
                    c.consts[item] = "int"
                continue
            m = re.match(r"(?:static\s+)?func\s+(\w+)\s*\((.*)\)\s*(?:->\s*([\w\[\]\.]+))?\s*:", ln)
            if m:
                params = []
                for p in split_top(m.group(2)):
                    if not p:
                        continue
                    pm = re.match(r"(\w+)\s*(?::\s*([\w\[\]\.]+))?\s*(:?=\s*.*)?$", p)
                    if pm:
                        params.append((pm.group(1), pm.group(2), bool(pm.group(3))))
                c.funcs[m.group(1)] = Func(m.group(1), params, m.group(3), nos[no - 1])
        classes[c.path] = c
    return classes


def resolve_type(name: str | None, cur: Cls) -> str | None:
    """Type name -> canonical ('res://x.gd' for project classes, builtin name otherwise)."""
    if not name:
        return None
    name = name.strip()
    if name.startswith("Array[") or name.startswith("Dictionary["):
        return name.split("[")[0]
    if name in cur.aliases:
        return cur.aliases[name]
    if name in cur.inner:
        return "inner:" + name
    return name


def parent_of(t: str, classes: dict[str, Cls]) -> str | None:
    if t.startswith("res://"):
        c = classes.get(t)
        if not c or not c.extends:
            return None
        e = c.extends
        if e.startswith("res://"):
            return e
        return e
    return PARENT.get(t)


def is_assignable(arg: str, param: str, classes: dict[str, Cls]) -> bool | None:
    """True / False when decidable, None when unknown."""
    if arg == param or param in ("Variant",) or arg == "Variant":
        return True
    if arg == "null":
        return not (param in SCALARS and param not in ("Callable", "Array", "Dictionary") and not param.startswith("Packed"))
    if arg == "int" and param == "float":
        return True
    if param == "StringName" and arg == "String" or param == "String" and arg == "StringName":
        return True
    if arg in SCALARS or param in SCALARS:
        if arg in SCALARS and param in SCALARS:
            return False if not (arg == "float" and param == "int") else True
        known_obj = lambda t: t.startswith("res://") or t in PARENT  # noqa: E731
        if (arg in SCALARS and known_obj(param)) or (param in SCALARS and known_obj(arg)):
            return False
        return None
    seen = set()
    cur: str | None = arg
    while cur and cur not in seen:
        if cur == param:
            return True
        seen.add(cur)
        cur = parent_of(cur, classes)
    # climbed to a root: decidable only when we know the whole chain of both
    known = lambda t: t.startswith("res://") or t in PARENT  # noqa: E731
    if known(arg) and known(param):
        return False
    return None


def ty(expr: str, cur: Cls, env: dict[str, str | None], classes: dict[str, Cls]) -> str | None:
    e = expr.strip()
    if not e:
        return None
    while e.startswith("(") and e.endswith(")") and len(split_top(e[1:-1], "\x00")) == 1 and _balanced(e[1:-1]):
        e = e[1:-1].strip()
    m = re.match(r"^(.*)\s+as\s+([\w\.]+)$", e)
    if m and _balanced(m.group(1)):
        return resolve_type(m.group(2), cur)
    if e in ("true", "false"):
        return "bool"
    if e == "null":
        return "null"
    if re.match(r"^-?\d+$", e) or re.match(r"^0x[0-9a-fA-F]+$", e):
        return "int"
    if re.match(r"^-?(\d+\.\d*|\.\d+|\d+(\.\d+)?e[-+]?\d+)$", e):
        return "float"
    if re.match(r'^(&|\^)?"[^"]*"$', e) or re.match(r"^'[^']*'$", e):
        return "String"
    if e.startswith("[") and e.endswith("]") and _balanced(e[1:-1]):
        return "Array"
    if e.startswith("{") and e.endswith("}") and _balanced(e[1:-1]):
        return "Dictionary"
    m = re.match(r"^(\w+)\.new\(.*\)$", e)
    if m and _balanced(e):
        return resolve_type(m.group(1), cur)
    m = re.match(r"^(\w+)\((.*)\)$", e)
    if m and _balanced(m.group(2)) and "(" not in m.group(1):
        fn = m.group(1)
        if fn in CONV:
            return CONV[fn]
        if fn in ("Vector2", "Vector3", "Color", "Vector2i", "Vector4", "Rect2", "AABB", "Transform3D", "Basis",
                  "PackedFloat32Array", "PackedByteArray", "Callable"):
            return fn
        f = find_func(fn, cur, classes)
        if f and f.ret:
            return resolve_type(f.ret, owner_of(fn, cur, classes) or cur)
        return None
    if re.match(r"^\w+$", e):
        if e == "self":
            return cur.path
        if e in env:
            return env[e]
        v = find_member(e, cur, classes)
        if v is not None:
            return v[0]
        if e in cur.aliases:
            return None
        return None
    # member chain a.b / a.b(...)
    idx = _last_top_dot(e)
    if idx > 0:
        base, rest = e[:idx], e[idx + 1:]
        bt = ty(base, cur, env, classes)
        if bt and bt.startswith("res://"):
            bc = classes.get(bt)
            if bc:
                mm = re.match(r"^(\w+)\s*(\(.*\))?$", rest)
                if mm:
                    name = mm.group(1)
                    if mm.group(2) is not None:
                        f = find_func(name, bc, classes)
                        if f and f.ret:
                            return resolve_type(f.ret, owner_of(name, bc, classes) or bc)
                    else:
                        v = find_member(name, bc, classes)
                        if v is not None:
                            return v[0]
    return None


def _balanced(s: str) -> bool:
    d = 0
    q = ""
    for i, c in enumerate(s):
        if q:
            if c == q and s[i - 1] != "\\":
                q = ""
        elif c in "\"'":
            q = c
        elif c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
            if d < 0:
                return False
    return d == 0


def _last_top_dot(s: str) -> int:
    d, q, last = 0, "", -1
    for i, c in enumerate(s):
        if q:
            if c == q and s[i - 1] != "\\":
                q = ""
        elif c in "\"'":
            q = c
        elif c in "([{":
            d += 1
        elif c in ")]}":
            d -= 1
        elif c == "." and d == 0 and not (i > 0 and s[i - 1].isdigit() and i + 1 < len(s) and s[i + 1].isdigit()):
            last = i
    return last


def base_chain(c: Cls, classes: dict[str, Cls]):
    seen = set()
    while c and c.path not in seen:
        yield c
        seen.add(c.path)
        c = classes.get(c.extends) if c.extends.startswith("res://") else None


def find_func(name: str, c: Cls, classes: dict[str, Cls]) -> Func | None:
    for k in base_chain(c, classes):
        if name in k.funcs:
            return k.funcs[name]
    return None


def owner_of(name: str, c: Cls, classes: dict[str, Cls]) -> Cls | None:
    for k in base_chain(c, classes):
        if name in k.funcs:
            return k
    return None


def find_member(name: str, c: Cls, classes: dict[str, Cls]):
    for k in base_chain(c, classes):
        if name in k.vars:
            return (resolve_type(k.vars[name], k),)
        if name in k.consts:
            return (resolve_type(k.consts[name], k),)
        if name in k.aliases:
            return (None,)
        if name in k.funcs:
            return ("Callable",)
    return None


def builtin_root(c: Cls, classes: dict[str, Cls]) -> str:
    last = c
    for k in base_chain(c, classes):
        last = k
    return last.extends


def check_file(c: Cls, classes: dict[str, Cls]) -> None:
    rel = c.path[len("res://"):]
    fname = rel
    in_func: Func | None = None
    env: dict[str, str | None] = {}
    func_indent = 0
    inh_builtin = builtin_root(c, classes)

    def err(no: int, msg: str) -> None:
        errors.append(f"{fname}:{no}: {msg}")

    for idx, ln in enumerate(c.lines):
        no = c.nos[idx]
        if not ln.strip():
            continue
        indent = len(ln) - len(ln.lstrip("\t"))
        body = ln.strip()
        m = re.match(r"(?:static\s+)?func\s+(\w+)", body) if indent == 0 else None
        if m:
            in_func = c.funcs.get(m.group(1))
            env = {}
            if in_func:
                for pn, pt, _d in in_func.params:
                    env[pn] = resolve_type(pt, c)
            func_indent = indent
            continue
        if indent == 0:
            in_func = None
            if re.match(r"(?:@\w+\s+)?var\s", body):
                # member var type annotations vs initialiser
                _check_var(no, body, c, env, classes, err)
            continue
        if in_func is None:
            continue
        # locals
        m = re.match(r"var\s+(\w+)\s*(?::\s*([\w\[\]\.]+))?\s*(:?=)?\s*(.*)$", body)
        if m:
            name, declared, assign, rhs = m.groups()
            if declared:
                env[name] = resolve_type(declared, c)
            elif assign == ":=":
                env[name] = ty(rhs, c, env, classes)
            else:
                env[name] = None
            _check_var(no, body, c, env, classes, err)
        m = re.match(r"for\s+(\w+)\s*(?::\s*(\w+))?\s+in\s+(.*):$", body)
        if m:
            env[m.group(1)] = resolve_type(m.group(2), c) if m.group(2) else None
        m = re.match(r"return\s+(.*)$", body)
        if m and in_func and in_func.ret and in_func.ret != "void":
            rt = ty(m.group(1), c, env, classes)
            want = resolve_type(in_func.ret, c)
            if rt and want and is_assignable(rt, want, classes) is False:
                err(no, f"return value should be {want} but is {rt} (in {in_func.name})")
        _check_calls(no, body, c, env, classes, err, inh_builtin)


def _check_var(no, body, c, env, classes, err) -> None:
    m = re.match(r"(?:@\w+(?:\([^)]*\))?\s+)*var\s+(\w+)\s*(?::\s*([\w\[\]\.]+))?\s*(:?=)\s*(.*)$", body)
    if not m:
        return
    name, declared, assign, rhs = m.groups()
    if declared and assign == "=":
        want = resolve_type(declared, c)
        got = ty(rhs, c, env, classes)
        if want and got and is_assignable(got, want, classes) is False:
            err(no, f"var {name}: {want} initialised with {got}")
    if not declared and assign == ":=" and _is_variant(rhs, c, env, classes):
        err(no, f"`var {name} :=` infers from a Variant ({rhs[:50]}): write the type, e.g. `var {name}: float = ...`")


def _is_variant(rhs: str, c: Cls, env, classes) -> bool:
    e = rhs.strip()
    if re.match(r"^\w+\(.*\)$", e) and e.split("(")[0] in CONV:
        return False
    if re.search(r"\bas\s+\w+\s*$", e):
        return False
    if re.match(r"^\w+\.new\(", e):
        return False
    # subscript of a Dictionary or untyped value at the end
    m = re.match(r"^(.*)\[[^\[\]]*\]$", e)
    if m and _balanced(m.group(1)):
        bt = ty(m.group(1), c, env, classes)
        if bt in ("Dictionary", "Array"):
            return True
        if bt is None and re.match(r"^[\w\.]+$", m.group(1)):
            base = m.group(1).split(".")[-1]
            decl = env.get(base)
            if decl is None and base in env:
                return False   # local of unknown inferred type: stay silent
            return False
    m = re.match(r"^(.*)\.get\(.*\)$", e)
    if m and _balanced(e) and ty(m.group(1), c, env, classes) == "Dictionary":
        return True
    return False


CALL_RE = re.compile(r"(?<![\w\"'])((?:[A-Za-z_]\w*)(?:\.[A-Za-z_]\w*)*)\(")


def _find_args(s: str, start: int) -> str | None:
    d = 0
    q = ""
    for i in range(start, len(s)):
        ch = s[i]
        if q:
            if ch == q and s[i - 1] != "\\":
                q = ""
            continue
        if ch in "\"'":
            q = ch
        elif ch in "([{":
            d += 1
        elif ch in ")]}":
            d -= 1
            if d == 0:
                return s[start + 1:i]
    return None


def _check_calls(no, body, c, env, classes, err, inh_builtin) -> None:
    # (X as T).member(...) patterns and plain chains
    for m in re.finditer(r"(\((?:[^()]|\([^()]*\))*\s+as\s+\w+\)|\b[A-Za-z_]\w*)((?:\.[A-Za-z_]\w*(?:\((?:[^()]|\([^()]*\))*\))?)+)", body):
        base_expr, chain = m.group(1), m.group(2)
        if m.start() > 0 and body[m.start() - 1] in ".":
            continue
        bt = ty(base_expr, c, env, classes)
        cur_t = bt
        pos = 0
        while cur_t and cur_t.startswith("res://") and pos < len(chain):
            mm = re.match(r"\.([A-Za-z_]\w*)(\()?", chain[pos:])
            if not mm:
                break
            name, is_call = mm.group(1), bool(mm.group(2))
            kc = classes.get(cur_t)
            if kc is None:
                break
            args = None
            end = pos + mm.end()
            if is_call:
                args = _find_args(chain, pos + mm.end() - 1)
                if args is None:
                    break
                end = pos + mm.end() - 1 + len(args) + 2
            known_root = builtin_root(kc, classes)
            f = find_func(name, kc, classes)
            v = find_member(name, kc, classes)
            if is_call:
                if f is None and v is None and name not in OBJECT_METHODS and known_root in ("RefCounted", "Object", ""):
                    err(no, f"no method '{name}' in {kc.path} (called on {base_expr})")
                elif f is not None:
                    _check_args(no, name, args, f, owner_of(name, kc, classes) or kc, c, env, classes, err)
                cur_t = resolve_type(f.ret, owner_of(name, kc, classes) or kc) if f and f.ret else None
            else:
                if v is None and f is None and name not in OBJECT_METHODS and known_root in ("RefCounted", "Object", ""):
                    err(no, f"no member '{name}' in {kc.path} (read on {base_expr})")
                cur_t = v[0] if v else None
            pos = end
    # bare calls into the same class
    for m in CALL_RE.finditer(body):
        name = m.group(1)
        if "." in name:
            continue
        if body[: m.start()].rstrip().endswith("func") or body[: m.start()].rstrip().endswith("."):
            continue
        f = find_func(name, c, classes)
        if f is None:
            continue
        args = _find_args(body, m.end() - 1)
        if args is not None:
            _check_args(no, name, args, f, owner_of(name, c, classes) or c, c, env, classes, err)


def _check_args(no, name, args, f: Func, owner: Cls, c: Cls, env, classes, err) -> None:
    given = split_top(args)
    given = [g for g in given if g != ""]
    maxn = len(f.params)
    minn = sum(1 for p in f.params if not p[2])
    if not (minn <= len(given) <= maxn):
        err(no, f"{name}() takes {minn}..{maxn} arguments, {len(given)} given (defined {owner.path}:{f.line})")
        return
    for i, g in enumerate(given):
        pname, ptype, _ = f.params[i]
        if not ptype:
            continue
        want = resolve_type(ptype, owner)
        got = ty(g, c, env, classes)
        if want and got and is_assignable(got, want, classes) is False:
            err(no, f"{name}(): argument {i + 1} ({pname}) should be {want} but is {got}")


def main() -> int:
    classes = load_classes()
    scan_all = "--all" in sys.argv
    n = 0
    for path, c in classes.items():
        rel = path[len("res://"):]
        if not scan_all and rel not in H12_FILES:
            continue
        check_file(c, classes)
        n += 1
    for e in errors:
        print("TYPE", e)
    print(f"gd types: {n} files scanned, {len(classes)} classes known: {'PASS' if not errors else str(len(errors)) + ' PROBLEM(S)'} (heuristic, NOT Godot)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
