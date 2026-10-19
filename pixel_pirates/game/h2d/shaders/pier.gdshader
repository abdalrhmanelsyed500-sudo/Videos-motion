// H2D-1.2 pier: two boxes (the deck and the T-head), 1 m above the water. The ground patch is NOT raised for the pier any
// more (the pier is stamped into the occluder channel only), so the deck is its own mesh with planks painted per pixel.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform float texel_m = 0.27778;

varying vec3 w_pos;
varying float v_up;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_up = NORMAL.y;
}

void fragment() {
	vec2 p = (floor(w_pos.xz / texel_m) + 0.5) * texel_m;
	vec3 base = vec3(0.4275, 0.2510, 0.1255);    // wood[2] #6d4020
	vec3 lite = vec3(0.5804, 0.4039, 0.1804);    // wood[3] #94672e
	vec3 dark = vec3(0.2902, 0.1569, 0.0784);    // wood[1] #4a2814
	vec3 pal;
	if (v_up > 0.5) {
		float plank = floor(p.y / 0.5);
		float hs = h2d_hash(vec2(plank, 4.0));
		pal = hs < 0.4 ? lite : (hs < 0.7 ? base : lite);
		if (fract(p.y / 0.5) < 0.12) {
			pal = dark;
		}
	} else {
		pal = dark * 1.2;
	}
	float ndl = v_up > 0.5 ? h2d_sun_dir.y : 0.35;
	float k = clamp(ndl, 0.0, 1.0);
	k = mix(floor(k * 4.0 + 0.5) / 4.0, k, 0.35);
	vec3 col = pal * (h2d_amb_col + h2d_sun_col * k);
	col *= 1.0 - 0.22 * h2d_rain;
	col *= h2d_cloud_shadow(w_pos.xz);
	col += pal * h2d_lamps(w_pos.xz) * 1.3;
	col = h2d_fog_mix(col, length(CAMERA_POSITION_WORLD - w_pos));
	ALBEDO = h2d_out(col);
}
