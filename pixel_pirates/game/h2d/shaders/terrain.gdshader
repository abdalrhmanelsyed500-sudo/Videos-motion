// H2D-1.2 island ground. ONE camera-following heightfield patch (2 m cells, ~80k triangles) and a procedural per-pixel ground:
// the biome class of the baked map picks a 5-step palette ramp, world-anchored noise picks the step (Bayer-dithered, so the
// steps blend like pixel art), and per-class patterns add ripples, tufts, strata, pebbles and cobbles. There is no albedo
// texture: the whole 4.4 km island costs two data textures (height, biome) and a 16 x 8 palette.
// Light: the same banded sun + ambient as every H2D shader, and sun shadows by marching the occluder height (canopy, houses,
// hills) in a dozen taps. Not run in Godot yet: see docs/H2D1_2_SCALE_AND_LAND.md.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform sampler2D height_tex : filter_nearest, repeat_disable;
uniform sampler2D biome_tex : filter_nearest, repeat_disable;
uniform sampler2D palette_tex : filter_nearest, repeat_disable;
uniform vec2 grid_origin = vec2(-2100.0, -3900.0);
uniform float grid_size = 4400.0;
uniform float cell_m = 2.0;
uniform float texel_m = 0.27778;     // size of one ground pixel in metres: 1 / 3.6 at sea, 1 / 14.4 ashore
uniform float shadow_steps = 10.0;
uniform float detail = 1.0;          // 1 = patterns and canopy shade, 0 = lean (Dev-Lite may use it)

varying vec3 w_pos;
varying float v_h;
varying vec3 v_n;

vec2 uv_of(vec2 xz) {
	return (xz - grid_origin) / grid_size;
}

float h_at(vec2 xz) {
	return h2d_dec_h(textureLod(height_tex, uv_of(xz), 0.0).r);
}

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float h = h_at(wp.xz);
	float hl = h_at(wp.xz - vec2(cell_m, 0.0));
	float hr = h_at(wp.xz + vec2(cell_m, 0.0));
	float hu = h_at(wp.xz - vec2(0.0, cell_m));
	float hd = h_at(wp.xz + vec2(0.0, cell_m));
	v_n = normalize(vec3(hl - hr, 2.0 * cell_m, hu - hd));
	v_h = h;
	VERTEX.y = max(h, -0.6);
	w_pos = vec3(wp.x, VERTEX.y, wp.z);
}

int bayer2(int x, int y) {
	return 2 * x + y * (3 - 4 * x);   // [[0, 2], [3, 1]]
}

// 4 x 4 ordered dither, 0..1
float bayer4(ivec2 c) {
	int x = c.x & 3;
	int y = c.y & 3;
	int b = bayer2(x & 1, y & 1) * 4 + bayer2((x >> 1) & 1, (y >> 1) & 1);
	return (float(b) + 0.5) / 16.0;
}

float hash_cell(vec2 c) {
	return h2d_hash(c + 11.7);
}

void fragment() {
	float h = v_h;
	if (h < 0.03) {
		discard;
	}
	vec2 p = (floor(w_pos.xz / texel_m) + 0.5) * texel_m;
	ivec2 tc = ivec2(floor(w_pos.xz / texel_m));
	// ragged class edges: the lookup is jittered by up to 1.3 m
	vec2 jit = (vec2(h2d_noise(p * 0.55), h2d_noise(p * 0.55 + 31.7)) - 0.5) * 2.6;
	vec4 bm = texture(biome_tex, uv_of(p + jit));
	int cls = int(floor(bm.r * 255.0 / 16.0 + 0.5));
	if (cls < 1) {
		cls = 1;
	}
	vec4 par = texelFetch(palette_tex, ivec2(5, cls), 0);
	float base = par.r * 4.0;
	float spread = par.g * 4.0;
	int pat = int(floor(par.b * 255.0 / 32.0 + 0.5));
	float n1 = h2d_noise(p / 1.7);
	float n2 = h2d_noise(p / 9.0 + 5.0);
	float n3 = h2d_noise(p / 40.0 + 9.0);
	float lvl = base + spread * ((n1 * 0.45 + n2 * 0.9 + n3 * 0.5) - 0.9);
	int accent = 0;
	if (detail > 0.5) {
		if (pat == 1) {                      // sand ripples: short dashes along the wind
			float rp = h2d_noise(vec2(p.x * 0.5 + 0.8 * n2, p.y * 3.2));
			if (rp > 0.74) {
				accent = 1;
			} else if (rp < 0.18) {
				accent = 2;
			}
		} else if (pat == 2) {               // grass tufts: little vertical strokes
			vec2 gc = floor(p / 0.9);
			vec2 lc = fract(p / 0.9);
			float hc = hash_cell(gc);
			if (hc > 0.80 && abs(lc.x - 0.5) < 0.09 && lc.y > 0.2 && lc.y < 0.8) {
				accent = lc.y < 0.5 ? 1 : 2;
			} else if (hc < 0.07 && length(lc - 0.5) < 0.14) {
				accent = 2;
			}
		} else if (pat == 3) {               // rock strata: bands with dark cracks
			float yy = p.y + 3.5 * h2d_noise(p * 0.12) + 0.8 * h2d_noise(p * 0.7);
			float band = floor(yy / 0.9);
			lvl += (hash_cell(vec2(band, 3.0)) - 0.5) * 1.8;
			if (fract(yy / 0.9) < 0.14) {
				accent = 1;
			}
		} else if (pat == 4) {               // pebbles
			vec2 gc = floor(p / 0.8);
			vec2 lc = fract(p / 0.8);
			float hc = hash_cell(gc + 3.1);
			float d = length(lc - vec2(0.5, 0.5));
			if (hc > 0.80 && d < 0.2) {
				accent = (lc.x + lc.y < 1.0) ? 1 : 2;
			}
		} else if (pat == 5) {               // cobbles: rows of 1.2 m stones with 1 px mortar
			float row = floor(p.y / 0.9);
			float xo = mod(row, 2.0) * 0.6;
			vec2 lc = vec2(fract((p.x + xo) / 1.2) * 1.2, fract(p.y / 0.9) * 0.9);
			float hc = hash_cell(vec2(floor((p.x + xo) / 1.2), row));
			lvl += (hc - 0.5) * 2.2;
			if (lc.x < max(texel_m, 0.05) * 1.2 || lc.y < max(texel_m, 0.05) * 1.2) {
				accent = 1;
			}
		}
		if (cls == 4 && bm.b < 0.99) {     // forest floor darkens under the canopy
			lvl -= 0.55 * bm.b;
		}
	}
	// the sea washes the sand: darker where the tide has been
	if (cls == 1) {
		lvl -= 1.5 * (1.0 - smoothstep(0.30, 0.62, h)) + 0.6 * (1.0 - smoothstep(0.62, 0.9, h));
	}
	float dth = bayer4(tc) - 0.5;
	int idx = int(clamp(floor(lvl + dth * 0.9 + 0.5), 0.0, 4.0));
	vec3 pal = texelFetch(palette_tex, ivec2(idx, cls), 0).rgb;
	if (accent > 0) {
		pal = texelFetch(palette_tex, ivec2(5 + accent, cls), 0).rgb;
	}
	vec3 n = normalize(v_n);
	float ndl = clamp(dot(n, h2d_sun_dir), 0.0, 1.0);
	float shadow = 1.0;
	vec2 hxz = h2d_sun_dir.xz;
	float hl = length(hxz);
	if (hl > 0.01 && ndl > 0.0) {
		vec2 hd = hxz / hl;
		float slope = h2d_sun_dir.y / hl;
		for (int i = 1; i <= 12; i++) {
			if (float(i) > shadow_steps) {
				break;
			}
			float sm = 2.0 * pow(1.5, float(i));
			vec2 q = w_pos.xz + hd * sm;
			float occ = h2d_dec_h(textureLod(height_tex, uv_of(q), 0.0).g);
			if (occ > h + slope * sm + 0.3) {
				shadow = 0.0;
				break;
			}
		}
	}
	float k = ndl * shadow;
	float banded = floor(k * 4.0 + 0.5) / 4.0;
	k = mix(banded, k, 0.35);
	vec3 col = pal * (h2d_amb_col + h2d_sun_col * k);
	col *= 1.0 - 0.22 * h2d_rain;
	col *= h2d_cloud_shadow(w_pos.xz);
	col += pal * h2d_lamps(w_pos.xz) * 1.3;
	float dist = length(CAMERA_POSITION_WORLD - w_pos);
	col = h2d_fog_mix(col, dist);
	ALBEDO = h2d_out(col);
}
