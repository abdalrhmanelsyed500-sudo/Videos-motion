// H2D-0 ship: ONE camera-facing quad that composites the baked hull layer and sail layer (sail wins where opaque).
// Texels are 1:1 with the art grid at the ship's distance. The quad is pulled toward the camera along its own view ray
// (identical on screen) so the ocean, which never writes depth, can never cut the hull.
shader_type spatial;
render_mode unshaded, skip_vertex_transform, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform sampler2D hull_tex : filter_nearest, repeat_disable;
uniform sampler2D sail_tex : filter_nearest, repeat_disable;
uniform vec2 hull_cell = vec2(0.0);   // column, row in the hull sheet
uniform vec2 sail_cell = vec2(0.0);   // column, row in the sail sheet
uniform vec2 hull_grid = vec2(16.0, 1.0);
uniform vec2 sail_grid = vec2(16.0, 5.0);
uniform vec2 frame_px = vec2(112.0, 96.0);
uniform vec2 pivot_px = vec2(56.0, 66.0);
uniform float m_per_px = 0.27778;
uniform float bob_m = 0.0;
uniform float depth_bias = 9.0;
uniform float sprite_light = 0.7;

varying vec2 v_uv;
varying float v_dist;
varying vec2 v_xz;

void vertex() {
	vec3 center_vs = (VIEW_MATRIX * MODEL_MATRIX * vec4(0.0, bob_m, 0.0, 1.0)).xyz;
	vec2 corner = vec2(UV.x * frame_px.x - pivot_px.x, -(UV.y * frame_px.y - pivot_px.y)) * m_per_px;
	vec3 vp = center_vs + vec3(corner, 0.0);
	float s = max((-vp.z - depth_bias) / max(-vp.z, 0.001), 0.1);
	VERTEX = vp * s;
	v_uv = UV;
	v_dist = length(vp);
	v_xz = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xz;
}

void fragment() {
	vec2 uv = clamp(v_uv, vec2(0.002), vec2(0.998));
	vec4 hu = texture(hull_tex, (hull_cell + uv) / hull_grid);
	vec4 sa = texture(sail_tex, (sail_cell + uv) / sail_grid);
	vec4 c = mix(hu, sa, step(0.5, sa.a));
	if (c.a < 0.5) {
		discard;
	}
	vec3 col = c.rgb * (h2d_amb_col + h2d_sun_col * sprite_light);
	col *= h2d_cloud_shadow(v_xz) * (1.0 - 0.15 * h2d_rain);
	col = h2d_fog_mix(col, v_dist);
	ALBEDO = h2d_out(col);
}
