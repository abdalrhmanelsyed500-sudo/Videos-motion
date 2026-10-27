extends RefCounted
class_name AGPalette
## Shared low-resolution palette and material helpers.

const COLORS := {
    "sky_top": "#5F8BEB",
    "sky_horizon": "#7D9EFC",
    "cloud": "#F2F5F5",
    "road": "#585260",
    "road_dark": "#454250",
    "yellow": "#D9B51F",
    "white": "#D8D9D1",
    "concrete": "#B4A992",
    "concrete_dark": "#8D8578",
    "sand": "#B9996D",
    "sand_light": "#D6B98B",
    "sand_dark": "#8F754F",
    "brick": "#A47F72",
    "brick_dark": "#8B665C",
    "window": "#30272E",
    "dash": "#272326",
    "dash_light": "#403A38",
    "gauge": "#DDD8C5",
    "needle": "#CE3C31",
    "magenta": "#A72C86",
    "red": "#C32228",
    "blue": "#37568A",
    "green": "#4F8E3A",
    "amber": "#E6B83B",
    "black": "#1B1B20",
    "metal": "#8C8D8A",
    "glass": "#5E7088",
    "palm": "#476B37",
    "leaf": "#3E6E38",
    "skin_light": "#C99768",
    "skin_mid": "#A9764B",
    "skin_dark": "#805234",
}

static func c(value: String) -> Color:
    if value.begins_with("#"):
        return Color.html(value)
    if COLORS.has(value):
        return Color.html(COLORS[value])
    return Color.MAGENTA

static func mat(value: String, unshaded := false, texture_path := "") -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = c(value)
    material.roughness = 1.0
    material.metallic = 0.0
    material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
    if unshaded:
        material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    else:
        material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
    if texture_path != "":
        var texture: Texture2D = load(texture_path)
        if texture != null:
            material.albedo_texture = texture
    return material

static func textured(value: String, texture_path: String, uv_scale := Vector3.ONE, unshaded := false) -> StandardMaterial3D:
    var material := mat(value, unshaded, texture_path)
    material.uv1_scale = uv_scale
    return material

static func vertex_colors(value: String = "#FFFFFF") -> StandardMaterial3D:
    var material := mat(value)
    material.vertex_color_use_as_albedo = true
    return material

static func billboard(texture_path: String, tint := "#FFFFFF") -> StandardMaterial3D:
    var material := mat(tint, true, texture_path)
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
    material.cull_mode = BaseMaterial3D.CULL_DISABLED
    material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
    material.alpha_scissor_threshold = 0.05
    return material
