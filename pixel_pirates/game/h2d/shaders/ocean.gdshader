// H2D-0 ocean: four analytic waves (same numbers as h2d/wave_model.gd), banded light, whitecaps, shallows and shore foam
// from the island's data texture, drifting cloud shadow, pack ice, rain rings, the ship's shadow, bow wave and wake.
// Drawn first and never writes depth, so sprites and the island always sit on top (see sea_view_3d.gd).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform vec4 w0;
uniform vec4 w1;
uniform vec4 w2;
uniform vec4 w3;
uniform vec3 deep_col = vec3(0.11, 0.37, 0.45);
uniform vec3 shallow_col = vec3(0.24, 0.55, 0.57);
uniform vec3 foam_col = vec3(0.93, 0.97, 0.97);
uniform vec3 lagoon_col = vec3(0.36, 0.72, 0.65);
uniform float wave_norm = 1.0;      // total amplitude, to normalise crest height
uniform float foam_amount = 0.3;    // 0..1 whitecap coverage
uniform float ice_cover = 0.0;
uniform float detail = 1.0;         // 1 = full detail (Standard/Ultra), 0 = Dev-Lite
uniform float posterize = 12.0;     // colour bands for the water body; 0 = off
uniform float sun_k = 1.0;          // how strongly the sun casts the ship's shadow
uniform sampler2D island_data : filter_linear, repeat_disable;
uniform vec2 island_origin = vec2(0.0);
uniform float island_size = 160.0;
uniform vec2 ship_pos = vec2(0.0);
uniform vec2 ship_dir = vec2(0.0, -1.0);
uniform float ship_speed = 0.0;     // scene metres per second
uniform float ship_len = 22.0;
uniform float ship_beam = 6.2;

varying vec3 w_pos;

void add_wave(vec4 w, vec2 p, inout float h, inout float dx, inout float dz) {
	float k = w.z;
	float ph = k * (w.x * p.x + w.y * p.y) - sqrt(9.81 * k) * h2d_time;
	h += w.w * sin(ph);
	float d = w.w * k * cos(ph);
	dx += d * w.x;
	dz += d * w.y;
}

vec3 wave_grad(vec2 p) {
	float h = 0.0;
	float dx = 0.0;
	float dz = 0.0;
	add_wave(w0, p, h, dx, dz);
	add_wave(w1, p, h, dx, dz);
	add_wave(w2, p, h, dx, dz);
	add_wave(w3, p, h, dx, dz);
	return vec3(h, dx, dz);
}

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 g = wave_grad(wp.xz);
	VERTEX.y += g.x;
	w_pos = vec3(wp.x, g.x, wp.z);
}

void fragment() {
	vec3 g = wave_grad(w_pos.xz);
	vec3 n = normalize(vec3(-g.y, 1.0, -g.z));
	if (detail > 0.5) {
		vec2 q = w_pos.xz * 0.7 + h2d_wind_to * h2d_time * 1.4;
		float r1 = h2d_noise(q) - 0.5;
		float r2 = h2d_noise(q * 2.1 + 7.0) - 0.5;
		n = normalize(n + vec3(r1, 0.0, r2) * (0.10 + 0.22 * h2d_storm));
	}
	vec3 to_cam = CAMERA_POSITION_WORLD - w_pos;
	float dist = length(to_cam);
	vec3 vdir = to_cam / max(dist, 0.001);
	float fres = pow(1.0 - clamp(dot(n, vdir), 0.0, 1.0), 3.0);
	float crest = clamp(g.x / max(wave_norm, 0.05) * 0.5 + 0.5, 0.0, 1.0);

	float depth_m = 99.0;
	float shore_m = 99.0;
	vec2 iuv = (w_pos.xz - island_origin) / island_size + 0.5;
	if (iuv.x > 0.0 && iuv.x < 1.0 && iuv.y > 0.0 && iuv.y < 1.0) {
		vec4 d = texture(island_data, iuv);
		depth_m = max(-(d.r * 48.0 - 8.0), 0.0);
		shore_m = d.b * 40.0;
	}
	vec3 col = mix(deep_col, shallow_col, clamp(crest * 0.5 + fres * 0.3, 0.0, 1.0));
	float shal = 1.0 - smoothstep(0.2, 6.0, depth_m);
	col = mix(col, lagoon_col, shal * 0.85);
	float ndl = clamp(dot(n, h2d_sun_dir), 0.0, 1.0);
	vec3 lightc = h2d_amb_col + h2d_sun_col * ndl;
	col *= lightc;
	col *= h2d_cloud_shadow(w_pos.xz);
	if (posterize > 1.0) {
		col = floor(col * posterize + 0.5) / posterize;
	}

	// pack ice: floes where a slow noise field rises above a threshold that falls as the cover grows
	if (ice_cover > 0.02) {
		float cell = h2d_fbm(w_pos.xz * 0.045 + 3.0) / 0.875;
		float thr = mix(0.85, 0.30, ice_cover);
		float floe = smoothstep(thr, thr + 0.03, cell);
		float rim = smoothstep(thr + 0.03, thr + 0.07, cell);
		vec3 icec = mix(vec3(0.62, 0.80, 0.90), vec3(0.93, 0.98, 1.0), h2d_noise(w_pos.xz * 0.5)) * lightc * 1.15;
		icec = mix(icec * 0.78, icec, rim);
		col = mix(col, icec, floe);
	}

	// foam: whitecaps, the shore line, bow wave and wake
	float foam = 0.0;
	float wc_noise = 0.0;
	if (detail > 0.5) {
		wc_noise = 0.18 * (h2d_noise(w_pos.xz * 0.9 + h2d_time * 0.3) - 0.5);
	}
	float wth = 0.80 - 0.20 * h2d_storm;
	foam = smoothstep(wth, wth + 0.12, crest + wc_noise) * clamp(foam_amount, 0.0, 1.0);
	float lap = shore_m - 0.9 * sin(h2d_time * 1.2 + shore_m * 0.7);
	foam = max(foam, (1.0 - smoothstep(0.0, 1.5, lap)) * step(0.001, shal));

	vec2 perp = vec2(-ship_dir.y, ship_dir.x);
	vec2 pr = w_pos.xz - ship_pos;
	float back = -dot(pr, ship_dir);
	float lat = abs(dot(pr, perp));
	float spd = clamp(ship_speed / 8.0, 0.0, 1.0);
	float wl = 55.0 * clamp(ship_speed / 25.0, 0.25, 1.4);
	if (spd > 0.0 && back > -14.0 && back < wl) {
		float t = clamp(back / wl, 0.0, 1.0);
		float width = 2.6 + max(back, 0.0) * 0.20;
		float arms = 1.0 - smoothstep(0.0, 0.9 + max(back, 0.0) * 0.03, abs(lat - width));
		float core = (1.0 - smoothstep(0.0, 2.2, lat)) * smoothstep(3.0, 8.0, back);
		float brk = h2d_noise(vec2(back * 0.35 - h2d_time * 2.0, lat * 0.9));
		float wk = (arms * 0.9 + core * 0.7) * (1.0 - t) * smoothstep(-2.0, 4.0, back);
		wk *= step(0.38, brk + 0.25 * (1.0 - t));
		float bow = (1.0 - smoothstep(0.0, 3.0, lat)) * smoothstep(-14.0, -9.0, back) * (1.0 - smoothstep(-8.0, -3.0, back));
		foam = max(foam, max(wk, bow * 0.8) * spd);
	}
	col = mix(col, foam_col * clamp(lightc * 1.3, vec3(0.55), vec3(1.1)), clamp(foam, 0.0, 1.0));

	// the ship's shadow slides away from the sun and lengthens as it sinks
	vec2 sd = -h2d_sun_dir.xz / max(h2d_sun_dir.y, 0.25) * 3.0;
	vec2 ps = w_pos.xz - ship_pos - sd;
	float al = dot(ps, ship_dir) / (ship_len * 0.52);
	float ac = dot(ps, perp) / (ship_beam * 0.55);
	float e = al * al + ac * ac;
	col *= 1.0 - 0.38 * (1.0 - smoothstep(0.5, 1.0, e)) * sun_k;

	if (detail > 0.5 && h2d_rain > 0.02) {
		vec2 cq = w_pos.xz * 0.5;
		vec2 cid = floor(cq);
		vec2 cf = fract(cq) - 0.5;
		float rnd = h2d_hash(cid);
		float ph = fract(h2d_time * 0.9 + rnd);
		float ring = smoothstep(0.07, 0.0, abs(length(cf) - ph * 0.5)) * (1.0 - ph) * step(rnd, h2d_rain * 0.9);
		col += vec3(ring * 0.35);
	}
	// sun glints: hard pixels, not a smooth highlight
	vec3 r = reflect(-h2d_sun_dir, n);
	float sp = pow(max(dot(r, vdir), 0.0), 90.0);
	float spk = step(0.5, sp) * step(0.45, h2d_hash(floor(w_pos.xz * 1.6 + floor(h2d_time * 3.0))));
	col += h2d_sun_col * 2.0 * spk * (1.0 - h2d_cloud * 0.9);

	col = h2d_fog_mix(col, dist);
	ALBEDO = h2d_out(col);
}
