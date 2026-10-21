// VP-0 sprite shadow: the sprite's own alpha silhouette, stood up on its pivot and flattened onto the ground along the sun direction.
// No shadow maps, no baked shadows: the direction follows the time of day for free, one quad per sprite (a MultiMesh in production).
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_disabled, blend_mix;

uniform sampler2D tex : filter_nearest;
uniform vec2 size_m = vec2(1.0);          // sprite size in metres
uniform vec2 pivot_m = vec2(0.5, 0.0);    // pivot: distance from the left and from the bottom, metres
uniform vec3 sun_dir = vec3(0.55, -0.75, -0.4);   // direction the light travels (toward the ground)
uniform vec4 shadow_colour : source_color = vec4(0.16, 0.09, 0.2, 0.42);
uniform float ground_y = 0.03;
uniform float max_len = 7.0;

void vertex() {
	vec3 piv = MODEL_MATRIX[3].xyz;
	float u = UV.x;
	float v = UV.y;                         // 0 = top
	float x = u * size_m.x - pivot_m.x;
	float h = (1.0 - v) * size_m.y - pivot_m.y;
	vec2 off = sun_dir.xz / max(-sun_dir.y, 0.15);
	float hh = max(h, 0.0);
	float len = min(hh * length(off), max_len);
	vec2 dir = normalize(off + vec2(1e-5));
	vec3 p = vec3(piv.x + x, ground_y, piv.z);
	p.xz += dir * len;
	// the part below the pivot is the footprint toward the viewer: keep it as a contact shadow
	p.z += max(-h, 0.0) * 0.55;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(p, 1.0);
}

void fragment() {
	float a = texture(tex, UV).a;
	if (a < 0.5) discard;
	ALBEDO = shadow_colour.rgb;
	ALPHA = shadow_colour.a;
}
