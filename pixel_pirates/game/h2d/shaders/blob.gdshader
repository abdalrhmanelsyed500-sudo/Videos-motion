// H2D-1.2 contact shadow under the pirate: a dark ellipse on the ground (alpha blended, no depth write).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform float strength = 0.38;

void fragment() {
	vec2 q = UV * 2.0 - 1.0;
	float d = dot(q, q);
	float a = (1.0 - smoothstep(0.55, 1.0, d)) * strength * (1.0 - 0.6 * h2d_overcast);
	ALBEDO = vec3(0.04, 0.05, 0.08);
	ALPHA = a;
}
