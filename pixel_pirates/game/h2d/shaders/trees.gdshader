// H2D-0 vegetation: every tree, bush and rock is one instance of a camera-facing quad (MultiMesh: ONE draw call).
// INSTANCE_CUSTOM.x = atlas cell index, .y = size scale. Same depth-bias trick as ship.gdshader.
shader_type spatial;
render_mode unshaded, skip_vertex_transform, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform sampler2D atlas : filter_nearest, repeat_disable;
uniform vec2 cell_px = vec2(48.0, 56.0);
uniform vec2 pivot_px = vec2(24.0, 52.0);
uniform vec2 atlas_grid = vec2(4.0, 2.0);
uniform float m_per_px = 0.27778;
uniform float depth_bias = 2.0;
uniform float sprite_light = 0.62;

varying vec2 v_uv;
varying vec2 v_cell;
varying float v_dist;
varying vec2 v_xz;

void vertex() {
	vec4 inst = MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0);
	vec3 center_vs = (VIEW_MATRIX * inst).xyz;
	float type = INSTANCE_CUSTOM.x;
	float sc = INSTANCE_CUSTOM.y;
	vec2 corner = vec2(UV.x * cell_px.x - pivot_px.x, -(UV.y * cell_px.y - pivot_px.y)) * m_per_px * sc;
	vec3 vp = center_vs + vec3(corner, 0.0);
	float s = max((-vp.z - depth_bias) / max(-vp.z, 0.001), 0.1);
	VERTEX = vp * s;
	v_uv = UV;
	v_cell = vec2(mod(type + 0.5, atlas_grid.x), floor((type + 0.5) / atlas_grid.x));
	v_dist = length(vp);
	v_xz = inst.xz;
}

void fragment() {
	vec2 uv = clamp(v_uv, vec2(0.002), vec2(0.998));
	vec4 c = texture(atlas, (floor(v_cell) + uv) / atlas_grid);
	if (c.a < 0.5) {
		discard;
	}
	vec3 col = c.rgb * (h2d_amb_col + h2d_sun_col * sprite_light);
	col *= h2d_cloud_shadow(v_xz) * (1.0 - 0.18 * h2d_rain);
	col = h2d_fog_mix(col, v_dist);
	ALBEDO = h2d_out(col);
}
