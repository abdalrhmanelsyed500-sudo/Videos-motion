// H2D-0.2 ship: ONE camera-facing quad that composites the baked hull layer and sail layer (sail wins where opaque).
// Texels are 1:1 with the art grid at the ship's distance. The quad is pulled toward the camera along its own view ray
// (identical on screen) so the ocean, which never writes depth, can never cut the hull.
// The sea and the wind act on the drawn ship here, in pixels: roll and pitch lean the mast (a shear that grows with height,
// worked out for the camera angle), the sails belly toward the lee with the wind and flutter when they luff or the air is
// light or gusty, and rain leaves bright specks on the canvas. The quad is padded by pad_px so a leaning mast is not clipped.
shader_type spatial;
render_mode unshaded, skip_vertex_transform, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform sampler2D hull_tex : filter_nearest, repeat_disable;
uniform sampler2D sail_tex : filter_nearest, repeat_disable;
uniform vec2 hull_cell = vec2(0.0);   // column, row in the hull sheet
uniform vec2 sail_cell = vec2(0.0);   // column, row in the sail sheet
uniform vec2 hull_grid = vec2(16.0, 1.0);
uniform vec2 sail_grid = vec2(16.0, 5.0);
uniform vec2 frame_px = vec2(112.0, 112.0);
uniform vec2 pivot_px = vec2(56.0, 66.0);
uniform float m_per_px = 0.27778;
uniform float bob_m = 0.0;
uniform float depth_bias = 9.0;
uniform float sprite_light = 0.7;
uniform vec2 lean = vec2(0.0);        // world (x, z) lean per metre of mast height: tan(roll) * starboard - tan(pitch) * forward
uniform float cam_cos = 0.669;        // cos of the camera pitch (a vertical mast is foreshortened by it)
uniform float cam_tan = 1.111;        // tan of the camera pitch
uniform float pad_px = 20.0;
uniform float billow_px = 0.0;        // how far the sail bellies at its fullest, in art pixels
uniform float flutter = 0.0;          // 0..1: luffing, slack or gusty canvas
uniform vec2 lee = vec2(1.0, 0.0);    // screen direction of the bulge (downwind): x east, y down the screen
uniform vec2 sail_span = vec2(11.0, 62.0);  // top and foot of the sail in the 112 px frame

varying vec2 v_uv;
varying float v_dist;
varying vec2 v_xz;

void vertex() {
	vec3 center_vs = (VIEW_MATRIX * MODEL_MATRIX * vec4(0.0, bob_m, 0.0, 1.0)).xyz;
	vec2 qpx = UV * (frame_px + vec2(2.0 * pad_px)) - vec2(pad_px);
	vec2 corner = vec2(qpx.x - pivot_px.x, -(qpx.y - pivot_px.y)) * m_per_px;
	float hgt = max(corner.y, 0.0);
	corner += vec2(lean.x / cam_cos, -lean.y * cam_tan) * hgt;
	vec3 vp = center_vs + vec3(corner, 0.0);
	float s = max((-vp.z - depth_bias) / max(-vp.z, 0.001), 0.1);
	VERTEX = vp * s;
	v_uv = qpx / frame_px;
	v_dist = length(vp);
	v_xz = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xz;
}

vec4 sheet(sampler2D tex, vec2 cell, vec2 grid, vec2 uv) {
	if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
		return vec4(0.0);
	}
	return texture(tex, (cell + clamp(uv, vec2(0.002), vec2(0.998))) / grid);
}

void fragment() {
	vec2 p = v_uv * frame_px;
	float t = clamp((p.y - sail_span.x) / (sail_span.y - sail_span.x), 0.0, 1.0);
	float prof = sin(3.14159 * t);                       // the sail is held at head and foot, so it bellies in the middle
	vec2 o = lee * billow_px * prof;
	o.x += flutter * 1.6 * sin(p.y * 0.55 + h2d_time * 13.0 + p.x * 0.12) * (0.35 + 0.65 * t);
	vec4 hu = sheet(hull_tex, hull_cell, hull_grid, v_uv);
	vec4 sa = sheet(sail_tex, sail_cell, sail_grid, (p - o) / frame_px);
	vec4 c = mix(hu, sa, step(0.5, sa.a));
	if (c.a < 0.5) {
		discard;
	}
	vec3 col = c.rgb * (h2d_amb_col + h2d_sun_col * sprite_light);
	col *= h2d_cloud_shadow(v_xz) * (1.0 - 0.15 * h2d_rain);
	// raindrops landing on the canvas and deck: sparse bright pixels that change a few times a second
	float speck = step(1.0 - 0.07 * h2d_rain, h2d_hash(floor(p) + floor(h2d_time * 9.0) * 17.0));
	col = mix(col, vec3(0.85, 0.92, 1.0) * clamp(dot(h2d_amb_col, vec3(0.33)) * 2.0 + 0.3, 0.3, 1.0), speck * 0.7);
	col = h2d_fog_mix(col, v_dist);
	ALBEDO = h2d_out(col);
}
