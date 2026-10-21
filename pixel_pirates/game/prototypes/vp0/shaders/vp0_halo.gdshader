// VP-0 light halo: an additive camera-facing disc with 4 stepped bands (pixel-art glow, not a smooth blur), flickering a little.
// Used for lanterns, windows and the fire ramp. One quad each; the real post-process bloom is optional on top.
shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, depth_test_disabled, cull_disabled;

uniform vec3 halo_colour = vec3(1.0, 0.62, 0.22);
uniform float intensity = 0.8;
uniform float radius_m = 1.6;
uniform float time_s = 0.0;
uniform float flicker = 0.12;
uniform float seed = 0.0;

void vertex() {
	mat4 mv = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	vec4 p = mv * vec4(VERTEX * radius_m * 2.0, 1.0);
	POSITION = PROJECTION_MATRIX * p;
}

void fragment() {
	float r = length(UV - vec2(0.5)) * 2.0;
	float f = 1.0 - flicker * (0.5 + 0.5 * sin(time_s * 9.0 + seed * 7.0) * sin(time_s * 5.3 + seed));
	float b = floor(clamp(1.0 - r, 0.0, 1.0) * 4.0) / 4.0;
	b = b * b;
	ALBEDO = halo_colour * b * intensity * f;
}
