// H2D-0.2 spray: real droplets in the 3D scene, two kinds in one MultiMesh.
//   * spindrift: streaks torn off wave crests and blown downwind. Only crests of a rough sea throw them (the density follows
//     the sea-state index), each one rides the live wave surface, and they are never launched on a timer.
//   * bursts: droplets thrown up when the hull meets the water hard (ship_motion.gd events at the bow or a rail). They fly on
//     a ballistic arc with the ship's speed and the wind added, and die when they touch the water again.
// Instance layout: [0, n_spin) spindrift, then 3 groups of n_burst droplets, one group per burst origin.
shader_type spatial;
render_mode unshaded, skip_vertex_transform, cull_disabled, depth_draw_never, blend_mix, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform float n_spin = 220.0;
uniform float n_burst = 28.0;
uniform vec2 focus = vec2(0.0);       // world (x, z) centre of the spindrift box (the camera focus)
uniform vec2 box = vec2(150.0, 110.0);
uniform vec2 wind_vel = vec2(0.0);    // spindrift speed, m/s (x east, z south)
uniform float spray_level = 0.0;      // 0..1 share of the spindrift that is alive: from the sea-state index
uniform float crest_min = 0.55;       // normalised crest height above which a wave may throw spindrift
uniform float wave_norm = 1.0;        // total wave amplitude
uniform vec4 burst_a0 = vec4(0.0);    // x, z of the origin, start time (h2d_time), power 0..1
uniform vec4 burst_a1 = vec4(0.0);
uniform vec4 burst_a2 = vec4(0.0);
uniform vec4 burst_b0 = vec4(0.0);    // outward direction (x, z) and the ship's own velocity (x, z)
uniform vec4 burst_b1 = vec4(0.0);
uniform vec4 burst_b2 = vec4(0.0);

varying vec2 v_uv;
varying float v_alpha;
varying float v_dist;

void vertex() {
	float fi = float(INSTANCE_ID);
	vec3 wpos = vec3(0.0);
	vec2 half_size = vec2(0.2);
	vec2 axis_vs = vec2(1.0, 0.0);
	float stretch = 0.0;
	float alpha = 0.0;
	if (fi < n_spin) {
		vec2 r = vec2(h2d_hash(vec2(fi, 3.1)), h2d_hash(vec2(fi, 7.7)));
		vec2 rel = mod(r * box + wind_vel * h2d_time * 0.9 - focus + box * 0.5, box);
		vec2 xz = focus - box * 0.5 + rel;
		float h = h2d_wave_h(xz);
		float cn = h / max(wave_norm, 0.05) * 0.5 + 0.5;
		float live = step(h2d_hash(vec2(fi, 13.3)), spray_level) * smoothstep(crest_min, crest_min + 0.2, cn);
		vec2 e = min(rel, box - rel) / (box * 0.12);
		live *= clamp(min(e.x, e.y), 0.0, 1.0);
		wpos = vec3(xz.x, h + 0.2 + 0.7 * h2d_hash(vec2(fi, 21.0)), xz.y);
		alpha = live * 0.75;
		half_size = vec2(0.2, 0.2);
		stretch = 0.9 + 0.8 * h2d_hash(vec2(fi, 5.5));
		axis_vs = (VIEW_MATRIX * vec4(wind_vel.x, 0.0, wind_vel.y, 0.0)).xy;
	} else {
		float bi = fi - n_spin;
		int g = int(floor(bi / n_burst));
		float i = bi - float(g) * n_burst;
		vec4 a = burst_a0;
		vec4 b = burst_b0;
		if (g == 1) {
			a = burst_a1;
			b = burst_b1;
		} else if (g == 2) {
			a = burst_a2;
			b = burst_b2;
		}
		float age = h2d_time - a.z - 0.12 * h2d_hash(vec2(i, 1.7));
		float life = 0.9 + 0.5 * h2d_hash(vec2(i, 2.9));
		float sp = (2.0 + 4.0 * h2d_hash(vec2(i, 4.1))) * (0.6 + 0.8 * a.w);
		float vy = (4.5 + 6.0 * h2d_hash(vec2(i, 6.3))) * (0.5 + 0.8 * a.w);
		vec2 side = vec2(-b.y, b.x);
		vec2 vh = b.xy * sp + side * (h2d_hash(vec2(i, 8.2)) - 0.5) * 5.0 + b.zw * 0.55 + wind_vel * 0.35;
		float y0 = h2d_wave_h(a.xy) + 0.6;
		vec2 xz = a.xy + vh * max(age, 0.0);
		float y = y0 + vy * age - 4.9 * age * age;
		float alive = step(0.0, age) * step(age, life) * step(0.01, a.w) * step(h2d_wave_h(xz) - 0.1, y);
		wpos = vec3(xz.x, y, xz.y);
		alpha = alive * (1.0 - smoothstep(0.55 * life, life, age)) * 0.9;
		half_size = vec2(0.22, 0.22);
		stretch = 0.0;
		axis_vs = (VIEW_MATRIX * vec4(vh.x, vy - 9.8 * age, vh.y, 0.0)).xy;
	}
	vec3 cv = (VIEW_MATRIX * vec4(wpos, 1.0)).xyz;
	vec2 ax = axis_vs / max(length(axis_vs), 0.0001);
	vec2 pp = vec2(-ax.y, ax.x);
	vec2 q = (UV - 0.5) * 2.0;
	vec3 pos = cv + vec3(ax * q.x * (half_size.x + stretch * 0.5) + pp * q.y * half_size.y, 0.0);
	if (alpha < 0.02) {
		pos = vec3(0.0, 0.0, 10.0);
	}
	VERTEX = pos;
	v_uv = UV;
	v_alpha = alpha;
	v_dist = -cv.z;
}

void fragment() {
	if (v_alpha < 0.02) {
		discard;
	}
	float lit = clamp(dot(h2d_amb_col, vec3(0.33)) * 1.8 + dot(h2d_sun_col, vec3(0.33)) * 0.6, 0.3, 1.1);
	vec3 col = vec3(0.92, 0.96, 1.0) * lit;
	float fogf = 1.0 - exp(-h2d_fog_density * max(v_dist - h2d_fog_start, 0.0) * 1.5);
	col = mix(col, h2d_fog_col, fogf);
	ALBEDO = h2d_out(col);
	ALPHA = v_alpha * (1.0 - 0.5 * fogf);
}
