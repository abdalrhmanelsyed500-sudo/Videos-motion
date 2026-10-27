extends RefCounted
class_name AGSettings
## Applies quality settings that can be changed without restarting the race.

static func apply() -> void:
    var loop: MainLoop = Engine.get_main_loop()
    if not (loop is SceneTree):
        return
    var tree: SceneTree = loop
    var root := tree.root
    var scale_value := clampf(float(AGState.get_setting("resolution_scale", 1.0)), 0.5, 1.0)
    for property in root.get_property_list():
        if String(property.get("name", "")) == "scaling_3d_scale":
            root.set("scaling_3d_scale", scale_value)
            break
    var quality := String(AGState.get_setting("quality", "medium"))
    var shadows := bool(AGState.get_setting("shadows", true)) and quality != "low"
    _set_shadows(root, shadows)

static func _set_shadows(node: Node, enabled: bool) -> void:
    if node is DirectionalLight3D:
        node.shadow_enabled = enabled
    for child in node.get_children():
        _set_shadows(child, enabled)
