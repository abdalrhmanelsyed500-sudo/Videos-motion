// H2D-0.2 ocean: four analytic waves with sea-state crest shaping (h2d_common.gdshaderinc = wave_model.gd), banded light,
// directional ripples, gust patches, whitecaps and wind-aligned foam lanes that grow with the sea state, shallows and shore
// foam from the island's data texture, drifting cloud shadow, pack ice, rain rings (the landing of the falling drops,
// see rain.gdshader), the ship's shadow, bow wave, wake, hull wash and slam foam.
// Drawn first and never writes depth, so sprites and the island always sit on top (see sea_view_3d.gd).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

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
uniform float ship_curve = 0.0;     // path curvature in 1/m, + = turning to starboard: bends the wake the way the ship turned
uniform float ship_len = 22.0;
uniform float ship_beam = 6.2;
uniform float ship_roll = 0.0;      // roll in units of 10 degrees, + = starboard side down (foam gathers on the low rail)
uniform float wash = 0.0;           // 0..1 water thrown up along the hull
uniform float slam = 0.0;           // 0..1 pulse after the bow hits a wave: an expanding foam ring at the bow
uniform float rain_cell_m = 3.4;    // the rain grid, same value as rain.gdshader so the rings match the drops
uniform float ring_k = 2.0;         // drops per cell that get a ring (effects budget)
uniform float normal_gain = 1.0;    // steeper shading as the sea builds

varying vec3 w_pos;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 g = h2d_wave(wp.xz);
	VERTEX.y += g.x;
	w_pos = vec3(wp.x, g.x, wp.z);
}

void fragment() {
	vec3 g = h2d_wave(w_pos.xz);
	vec2 spr = w_pos.xz - ship_pos;
	// a gust patch is a drifting darker, rougher area; it is guaranteed over the ship while a gust blows
	float gp = 0.0;
	if (h2d_gust > 0.02) {
		float gthr = mix(0.80, 0.45, h2d_gust) - 0.25 * (1.0 - smoothstep(10.0, 70.0, length(spr)));
		gp = smoothstep(gthr, gthr + 0.22, h2d_noise(w_pos.xz * 0.02 - h2d_adv * 0.02)) * h2d_gust;
	}
	vec3 n = normalize(vec3(-g.y * normal_gain, 1.0, -g.z * normal_gain));
	// ripples drift downwind with the air; they roughen with the sea state and inside a gust
	vec2 rq = w_pos.xz - h2d_adv * 0.5;
	float rg = 0.05 + 0.20 * h2d_sea + 0.35 * gp;
	float r1 = h2d_noise(rq * 0.8) - 0.5;
	float r2 = 0.0;
	if (detail > 0.5) {
		r2 = h2d_noise(rq * 2.1 + 7.0) - 0.5;
	} else {
		r2 = h2d_noise(rq * 1.7 + 7.0) - 0.5;
	}
	n = normalize(n + vec3(r1, 0.0, r2) * rg);
	vec3 to_cam = CAMERA_POSITION_WORLD - w_pos;
	float dist = length(to_cam);
	vec3 vdir = to_cam / max(dist, 0.001);
	float fres = pow(1.0 - clamp(dot(n, vdir), 0.0, 1.0), 3.0);
	float crest_h = clamp(g.x / max(wave_norm, 0.05) * 0.5 + 0.5, 0.0, 1.0);

	float depth_m = 99.0;
	float shore_m = 99.0;
	vec2 iuv = (w_pos.xz - island_origin) / island_size + 0.5;
	if (iuv.x > 0.0 && iuv.x < 1.0 && iuv.y > 0.0 && iuv.y < 1.0) {
		vec4 d = texture(island_data, iuv);
		depth_m = max(-(d.r * 48.0 - 8.0), 0.0);
		shore_m = d.b * 40.0;
	}
	vec3 col = mix(deep_col, shallow_col, clamp(crest_h * 0.5 + fres * 0.3, 0.0, 1.0));
	float shal = 1.0 - smoothstep(0.2, 6.0, depth_m);
	col = mix(col, lagoon_col, shal * 0.85);
	float ndl = clamp(dot(n, h2d_sun_dir), 0.0, 1.0);
	vec3 lightc = h2d_amb_col + h2d_sun_col * ndl;
	col *= lightc;
	col *= h2d_cloud_shadow(w_pos.xz);
	col *= 1.0 - 0.22 * gp;
	col = mix(col, vec3(dot(col, vec3(0.333))) * 0.95, 0.25 * h2d_rain);
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
	float wth = mix(0.92, 0.62, h2d_sea);
	foam = smoothstep(wth, wth + 0.12, crest_h + wc_noise) * clamp(foam_amount, 0.0, 1.0);
	// wind-aligned foam lanes: short dashes in a grid, each turned along the wind, drifting downwind. Calm sea: none.
	float lane_k = smoothstep(0.30, 0.80, h2d_sea);
	if (lane_k > 0.01) {
		vec2 lp = w_pos.xz - h2d_adv * 0.8;
		vec2 lc = floor(lp / 14.0);
		vec2 c0 = (lc + vec2(0.35) + 0.3 * vec2(h2d_hash(lc), h2d_hash(lc + 3.3))) * 14.0;
		vec2 dv = lp - c0;
		float la = dot(dv, h2d_wind_to);
		float lt = dot(dv, vec2(-h2d_wind_to.y, h2d_wind_to.x));
		float llen = 2.2 + 1.6 * h2d_hash(lc + 8.8);
		float dash = (1.0 - smoothstep(llen * 0.6, llen, abs(la))) * (1.0 - smoothstep(0.22, 0.5, abs(lt)));
		foam = max(foam, dash * step(h2d_hash(lc + 5.5), lane_k * 0.85) * (0.55 + 0.45 * crest_h));
	}
	float lap = shore_m - 0.9 * sin(h2d_time * 1.2 + shore_m * 0.7);
	foam = max(foam, (1.0 - smoothstep(0.0, 1.5, lap)) * step(0.001, shal));

	vec2 perp = vec2(-ship_dir.y, ship_dir.x);
	vec2 pr = w_pos.xz - ship_pos;
	float back = -dot(pr, ship_dir);
	float behind = max(back, 0.0);
	float lat = abs(dot(pr, perp) + 0.5 * ship_curve * behind * behind);
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
	// water thrown along the hull (more on the rail that is rolled down) and the ring after the bow slams into a wave
	float hl_a = dot(pr, ship_dir);
	float hl_s = dot(pr, perp);
	float hull = (1.0 - smoothstep(ship_beam * 0.5, ship_beam * 0.5 + 1.8, abs(hl_s))) * (1.0 - smoothstep(ship_len * 0.5, ship_len * 0.5 + 3.0, abs(hl_a)));
	float hw_n = step(0.5, h2d_noise(vec2(hl_a * 0.7 + h2d_time * 2.5, hl_s * 0.9)));
	foam = max(foam, hull * wash * hw_n * clamp(1.0 + ship_roll * clamp(hl_s / 3.0, -1.0, 1.0), 0.2, 1.6));
	if (slam > 0.02) {
		vec2 bv = pr - ship_dir * ship_len * 0.42;
		float brad = 1.5 + 9.0 * (1.0 - slam);
		float bring = (1.0 - smoothstep(0.0, 1.7, abs(length(bv) - brad))) * smoothstep(-5.0, 1.5, dot(bv, ship_dir));
		foam = max(foam, slam * bring * step(0.3, h2d_noise(bv * 0.9 + h2d_time)));
	}
	col = mix(col, foam_col * clamp(lightc * 1.3, vec3(0.55), vec3(1.1)), clamp(foam, 0.0, 1.0));

	// the ship's shadow slides away from the sun and lengthens as it sinks
	vec2 sd = -h2d_sun_dir.xz / max(h2d_sun_dir.y, 0.25) * 3.0;
	vec2 ps = w_pos.xz - ship_pos - sd;
	float al = dot(ps, ship_dir) / (ship_len * 0.52);
	float ac = dot(ps, perp) / (ship_beam * 0.55);
	float e = al * al + ac * ac;
	col *= 1.0 - 0.38 * (1.0 - smoothstep(0.5, 1.0, e)) * sun_k;

	// rain rings: every ring is the landing of a drop that rain.gdshader draws falling (same cell, same hash, same phase)
	if (h2d_rain > 0.02 && ring_k > 0.5) {
		vec2 rcell = floor(w_pos.xz / rain_cell_m);
		float rain_c = h2d_rain_local((rcell + 0.5) * rain_cell_m);
		float acc = 0.0;
		for (int k = 0; k < 3; k++) {
			float kf = float(k);
			if (kf >= ring_k - 0.5) {
				break;
			}
			float tt = h2d_time / DROP_PERIOD + h2d_drop_phase(rcell, kf);
			float cyc = floor(tt);
			float u = tt - cyc;
			// the ring belongs to the drop that LANDED: this cycle's drop once u passes the fall, otherwise the last one
			float seed = h2d_drop_seed(kf, cyc - step(u, DROP_FALL_FRAC));
			float on = step(h2d_drop_on(rcell, seed), rain_c);
			float since = fract(u - DROP_FALL_FRAC) * DROP_PERIOD;
			float splashing = step(since, 0.6);
			float rr = length(w_pos.xz - h2d_drop_impact(rcell, seed, rain_cell_m));
			float ring = (1.0 - smoothstep(0.08, 0.2, abs(rr - since * 0.65))) * (1.0 - since / 0.6);
			float core = step(rr, 0.3) * step(since, 0.12);
			acc += on * splashing * (ring * 0.55 + core * 0.9);
		}
		col += vec3(clamp(acc, 0.0, 1.0) * 0.4);
	}
	// sun glints: hard pixels, not a smooth highlight
	vec3 r = reflect(-h2d_sun_dir, n);
	float sp = pow(max(dot(r, vdir), 0.0), 90.0);
	float spk = step(0.5, sp) * step(0.45, h2d_hash(floor(w_pos.xz * 1.6 + floor(h2d_time * 3.0))));
	col += h2d_sun_col * 2.0 * spk * (1.0 - h2d_cloud * 0.9);

	col = h2d_fog_mix(col, dist);
	ALBEDO = h2d_out(col);
}
