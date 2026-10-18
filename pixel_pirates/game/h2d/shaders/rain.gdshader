// H2D-0.3 rain: real falling drops in the 3D scene (not a screen filter). One MultiMesh quad per (cell, k) slot; each drop
// falls from a height to a landing point ON the wave surface, carried sideways by the wind, then shows a small splash crown.
// The landing point, phase, period and "is it raining here" come from h2d_common.gdshaderinc, the same functions the ocean
// shader uses for its rings, so the rings you see on the water are the drops you saw fall.
// What changed in H2D-0.3 (the rain looked unnatural: even, mechanical, all one kind):
//   * every slot has its own period, so the rain never pulses in step; every drop has its own size, speed and brightness
//   * the drop is a two-tone pixel streak (bright head, dim tail); a few drops (the "near" tier) are brighter
//   * the slant follows the wind, but it is the MEAN wind everywhere and gets MORE slant inside the dark gust patch on the
//     water (h2d_gust_field, the same field the ocean darkens), plus slow eddies, so a gust visibly bends the rain where it
//     blows and the drops of one neighbourhood lean the same way
//   * light rain is sparse, short and nearly upright; a downpour is dense, long and slanted, in sheets (h2d_rain_local)
//   * far drops fade (depth), the fog hides them like everything else
// Instance layout: INSTANCE_ID = slot k * (grid.x * grid.y) + row * grid.x + column; sea_view_3d.gd builds the MultiMesh.
shader_type spatial;
render_mode unshaded, skip_vertex_transform, cull_disabled, depth_draw_never, blend_mix, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform vec2 grid = vec2(56.0, 44.0);
uniform vec2 base_cell = vec2(0.0);   // integer cell of the grid's first column/row (follows the camera focus)
uniform float cell_m = 3.4;
uniform float fall_ms = 19.0;         // fall speed, m/s
uniform vec2 drift = vec2(0.0);       // sideways speed of the drops in the mean wind, m/s
uniform float gust_bend = 0.8;        // how much more the rain leans inside the gust patch (0 = not at all)
uniform float streak_m = 1.5;         // length of an average streak, m (grows with the rain intensity)
uniform float half_w = 0.2;           // half width of the streak, m (0.4 m is about 1.4 px at the art grid, so it never falls between pixels)
uniform float alpha_k = 0.7;          // overall opacity (grows with the rain intensity)
uniform float splash_k = 1.0;         // size of the splash crown (smaller in light rain)
uniform vec3 rain_col = vec3(0.74, 0.84, 0.94);

varying vec2 v_uv;
varying float v_alpha;
varying float v_kind;
varying float v_dist;
varying float v_tier;

// sideways speed of a drop that lands at xz: mean wind, more lean in the gust patch, slow eddies
vec2 rain_drift(vec2 xz) {
	float gf = h2d_gust_field(xz);
	float sp = length(drift);
	vec2 eddy = vec2(h2d_noise(xz * 0.03 - h2d_adv * 0.03), h2d_noise(xz * 0.03 + 37.0 - h2d_adv * 0.03)) - vec2(0.5);
	return drift * (1.0 + gust_bend * gf) + eddy * sp * 0.6;
}

void vertex() {
	int nx = int(grid.x);
	int per = nx * int(grid.y);
	int kk = INSTANCE_ID / per;
	int rem = INSTANCE_ID - kk * per;
	int iz = rem / nx;
	int ix = rem - iz * nx;
	vec2 cell = base_cell + vec2(float(ix), float(iz));
	float k = float(kk);
	float period = h2d_drop_period(cell, k);
	float tt = h2d_time / period + h2d_drop_phase(cell, k);
	float cyc = floor(tt);
	float u = tt - cyc;
	float seed = h2d_drop_seed(k, cyc);
	float on = step(h2d_drop_on(cell, seed), h2d_rain_local((cell + 0.5) * cell_m) * h2d_rain_dens);
	vec2 imp = h2d_drop_impact(cell, seed, cell_m);
	float dv = h2d_drop_var(cell, seed);
	float surf = h2d_wave_h(imp);
	float fall_t = period * DROP_FALL_FRAC;
	float ft = clamp(u / DROP_FALL_FRAC, 0.0, 1.0);
	float tau = (1.0 - ft) * fall_t;                       // seconds until it lands
	float fall = fall_ms * mix(0.88, 1.12, dv);
	vec2 dr = rain_drift(imp);
	float spd = length(vec2(fall, length(dr)));
	float tau2 = tau + streak_m * mix(0.7, 1.3, dv) / spd;
	vec3 head = vec3(imp.x - dr.x * tau, surf + fall * tau, imp.y - dr.y * tau);
	vec3 tail = vec3(imp.x - dr.x * tau2, surf + fall * tau2, imp.y - dr.y * tau2);
	float falling = step(u, DROP_FALL_FRAC);
	float since = clamp((u - DROP_FALL_FRAC) * period / SPLASH_T, 0.0, 1.0);   // 0..1 through the splash
	vec3 hv = (VIEW_MATRIX * vec4(head, 1.0)).xyz;
	vec3 tv = (VIEW_MATRIX * vec4(tail, 1.0)).xyz;
	vec3 pos;
	float alpha;
	if (falling > 0.5) {
		vec3 d = hv - tv;
		vec3 axis = d / max(length(d), 0.0001);
		vec3 side = normalize(cross(axis, hv));
		pos = mix(hv, tv, UV.y) + side * (UV.x - 0.5) * 2.0 * half_w;
		// the drop fades in during the first part of its fall, so it never pops into existence
		alpha = smoothstep(0.0, 0.12, ft);
	} else {
		vec3 c = (VIEW_MATRIX * vec4(imp.x, surf + 0.25 * splash_k, imp.y, 1.0)).xyz;
		float grow = (0.55 + 0.9 * since) * splash_k;
		pos = c + vec3((UV.x - 0.5) * 1.1 * grow, (0.5 - UV.y) * 0.8 * grow, 0.0);
		alpha = (1.0 - since) * 0.8;
	}
	v_uv = UV;
	v_kind = 1.0 - falling;
	v_dist = -hv.z;
	v_tier = mix(0.62, 1.0, step(0.7, dv));                // about one drop in three is a bright, near one
	v_alpha = alpha * on;
	if (on < 0.5) {
		pos = vec3(0.0, 0.0, 10.0);
	}
	VERTEX = pos;
}

void fragment() {
	float a = v_alpha;
	if (v_kind > 0.5) {
		// splash crown: a small blob of pixels that rises and fades
		vec2 q = v_uv - vec2(0.5, 0.80);
		a *= step(length(q * vec2(1.0, 1.6)), 0.34) * step(q.y, 0.06);
	} else {
		// two-tone streak: a bright head (the first 30%), a dim tail, hard edges like the rest of the pixel art
		a *= step(abs(v_uv.x - 0.5), 0.46) * mix(0.42, 1.0, step(v_uv.y, 0.30)) * v_tier;
	}
	if (a < 0.05) {
		discard;
	}
	float lit = clamp(dot(h2d_amb_col, vec3(0.33)) * 1.7 + dot(h2d_sun_col, vec3(0.33)) * 0.5, 0.22, 1.0);
	vec3 col = rain_col * lit;
	float fogf = 1.0 - exp(-h2d_fog_density * max(v_dist - h2d_fog_start, 0.0) * 1.5);
	col = mix(col, h2d_fog_col, fogf);
	float depth_k = 1.0 - 0.4 * smoothstep(170.0, 240.0, v_dist);   // the far drops are dimmer
	ALBEDO = h2d_out(col);
	ALPHA = a * (1.0 - 0.5 * fogf) * alpha_k * depth_k;
}
