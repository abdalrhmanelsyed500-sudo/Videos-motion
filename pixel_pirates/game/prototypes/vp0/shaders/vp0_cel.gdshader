// VP-0 cel shader for the few real 3D surfaces (hull, deck, sails): textured with pixel-art tiles (nearest), lit by ONE directional light,
// the lighting is quantised to 4 bands that slide along a warm-light / cool-shadow tint, exactly like the baked sprites.
shader_type spatial;
render_mode unshaded, cull_disabled;

uniform sampler2D albedo_tex : filter_nearest, repeat_enable;
uniform vec3 sun_dir = vec3(0.55, -0.75, -0.4);
uniform vec3 light_tint = vec3(1.0);
uniform vec3 shadow_tint = vec3(0.78, 0.74, 0.95);
uniform float band_gain = 1.0;
uniform float back_glow = 0.0;     // sails: light seen through the cloth from behind
uniform vec4 tint : source_color = vec4(1.0);

void fragment() {
	vec4 c = texture(albedo_tex, UV);
	vec3 n = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	bool front = FRONT_FACING;
	if (!front) n = -n;
	float ndl = dot(n, -normalize(sun_dir));
	float band = floor(clamp(ndl * 0.5 + 0.55, 0.0, 0.999) * 4.0);
	float m[4] = float[4](0.58, 0.78, 0.98, 1.12);
	vec3 s = mix(shadow_tint, vec3(1.0), clamp(band / 3.0 + 0.2, 0.0, 1.0));
	vec3 col = c.rgb * tint.rgb * s * m[int(band)] * band_gain;
	if (!front) col = mix(col, c.rgb * vec3(1.05, 0.98, 0.85), back_glow);
	ALBEDO = col * light_tint;
	ALPHA = c.a;
}
