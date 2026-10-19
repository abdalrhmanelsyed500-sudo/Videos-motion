// H2D-0/H2D-1 island ground: a heightfield mesh, flat pixel-art albedo, per-pixel banded light from the baked normal map, and
// sun shadows from hills and trees by ray-marching the height data (no shadow maps: cheap on Dev-Lite).
// Texture channels: data.r = height (-8..40 m), data.g = height including tree canopies (the shadow caster).
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform sampler2D albedo_tex : filter_nearest, repeat_disable;
uniform sampler2D data_tex : filter_nearest, repeat_disable;
uniform sampler2D normal_tex : filter_nearest, repeat_disable;
uniform float island_size = 240.0;
uniform float shadow_steps = 10.0;

varying vec2 v_uv;
varying vec3 w_pos;

void vertex() {
	// UV from the local position (column = east, row = south), so it never depends on PlaneMesh's UV orientation
	vec2 uv = VERTEX.xz / island_size + 0.5;
	float h = textureLod(data_tex, uv, 0.0).r * 48.0 - 8.0;
	VERTEX.y = max(h, -0.6);
	v_uv = uv;
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 d = texture(data_tex, v_uv);
	float h = d.r * 48.0 - 8.0;
	vec4 a = texture(albedo_tex, v_uv);
	if (h < 0.03 || a.a < 0.5) {
		discard;
	}
	vec3 n = normalize(texture(normal_tex, v_uv).rgb * 2.0 - 1.0);
	float ndl = clamp(dot(n, h2d_sun_dir), 0.0, 1.0);
	float shadow = 1.0;
	vec2 hxz = h2d_sun_dir.xz;
	float hl = length(hxz);
	if (hl > 0.01) {
		vec2 hd = hxz / hl;
		float slope = h2d_sun_dir.y / hl;
		for (int i = 1; i <= 12; i++) {
			if (float(i) > shadow_steps) {
				break;
			}
			float sm = 0.8 * pow(1.38, float(i));
			vec2 suv = v_uv + hd * sm / island_size;
			if (suv.x < 0.0 || suv.x > 1.0 || suv.y < 0.0 || suv.y > 1.0) {
				break;
			}
			float occ = textureLod(data_tex, suv, 0.0).g * 48.0 - 8.0;
			if (occ > h + slope * sm + 0.25) {
				shadow = 0.0;
				break;
			}
		}
	}
	float k = ndl * shadow;
	float banded = floor(k * 4.0 + 0.5) / 4.0;
	k = mix(banded, k, 0.35);
	vec3 col = a.rgb * (h2d_amb_col + h2d_sun_col * k);
	col *= 1.0 - 0.22 * h2d_rain;
	col *= h2d_cloud_shadow(w_pos.xz);
	col += a.rgb * h2d_lamps(w_pos.xz) * 1.3;   // night: warm pools on the planks and the plaza
	float dist = length(CAMERA_POSITION_WORLD - w_pos);
	col = h2d_fog_mix(col, dist);
	ALBEDO = h2d_out(col);
}
