// VP-0 ocean: ONE plane, ONE pass, no render targets. Pixel-art water: banded depth colour with ordered dither, sand seen through the
// shallows, contour-line waves, glints, shore foam and ship wake. Everything is computed on the 24 px/m art-pixel grid (snapped world position),
// so it keeps its pixel size at any window size. Cost: 1 signed-distance fetch, 3 noise fetches, 1 bed-tile fetch. No screen texture, no depth texture.
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_disabled;

uniform sampler2D depth_tex : filter_linear, repeat_disable;
uniform sampler2D noise_tex : filter_linear, repeat_enable;
uniform sampler2D bed_atlas : filter_nearest, repeat_disable;
uniform float tile_m = 2.0;
uniform vec4 depth_rect = vec4(-52.0, -39.0, 104.0, 78.0);   // x0, z0, w, h in metres
uniform vec2 depth_range = vec2(-4.0, 20.0);
uniform float ppm = 24.0;                                      // art pixels per metre on the ground
uniform float time_s = 0.0;
uniform vec3 ramp[7];                                          // deep -> shallow (palette ramps sea_deep / sea_mid / lagoon)
uniform vec3 foam[4];                                          // palette ramp "foam"
uniform vec3 light_tint = vec3(1.0);
uniform vec3 fog_colour = vec3(0.55, 0.7, 0.72);
uniform float fog_amount = 0.0;
uniform float glint = 1.0;
uniform float bed_row = 6.0;
uniform vec2 ship_pos = vec2(1e5);
uniform vec2 ship_fwd = vec2(1.0, 0.0);
uniform vec2 ship_half = vec2(11.0, 3.1);
uniform float ship_speed = 0.0;

varying vec3 wpos;

float bayer4(vec2 p) {
	ivec2 i = ivec2(mod(p, 4.0));
	int idx = i.x + i.y * 4;
	float m[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	return (m[idx] + 0.5) / 16.0;
}

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

vec3 pick(float t) {
	int i = clamp(int(floor(t)), 0, 6);
	return ramp[i];
}

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 q = (floor(wpos.xz * ppm) + 0.5) / ppm;
	float t = time_s;
	vec2 duv = (q - depth_rect.xy) / depth_rect.zw;
	float dn = texture(depth_tex, duv).r;
	float d = mix(depth_range.x, depth_range.y, dn);
	if (duv.x < 0.0 || duv.y < 0.0 || duv.x > 1.0 || duv.y > 1.0) d = depth_range.y;
	// wobble the coastline so it is not a smooth distance iso-line
	float n1 = texture(noise_tex, q * 0.045 + vec2(t * 0.010, t * 0.006)).r;
	float n2 = texture(noise_tex, q * 0.090 + vec2(-t * 0.008, t * 0.012)).g;
	float n3 = texture(noise_tex, q * vec2(0.50, 1.05) + vec2(t * 0.05, 0.0)).b;
	d += (n2 - 0.5) * 0.9;
	float dd = max(d, 0.0);
	// depth colour index 0 (deep) .. 6 (shallow)
	float depth01 = clamp(log2(1.0 + dd) / log2(17.0), 0.0, 1.0);
	float ti = (1.0 - depth01) * 6.0 + (n1 - 0.5) * 0.55;
	float dith = bayer4(FRAGCOORD.xy);
	float base_t = floor(ti) + (fract(ti) > dith ? 1.0 : 0.0);
	vec3 col = pick(base_t);
	// contour waves: thin light and dark lines on iso-lines of two moving noise fields
	float w = n1 * 0.62 + n2 * 0.38;
	float lines = fract(w * 9.0);
	float shade_up = step(lines, 0.07);
	float shade_dn = step(abs(lines - 0.5), 0.045);
	col = mix(col, pick(base_t + 1.0), shade_up * 0.9);
	col = mix(col, pick(base_t - 1.0), shade_dn * 0.8);
	// short glints (horizontal dashes), mostly in deeper water
	float dash = step(0.80, n3) * step(0.40, n2);
	col = mix(col, pick(base_t + 1.0), dash * 0.8);
	// sparkles: single pixels, changing 3 times a second
	float sp = hash21(floor(q * ppm) + floor(t * 3.0) * 17.0);
	col = mix(col, foam[3], step(0.9982 - 0.0016 * glint, sp) * step(0.5, n1));
	// sand seen through the shallows
	float bed_a = 1.0 - smoothstep(0.9, 3.4, d + (n1 - 0.5) * 0.8);
	vec2 tuv = fract(q / tile_m);
	ivec2 tp = ivec2(floor(tuv * 48.0));
	ivec2 var_ = ivec2(int(mod(floor(q.x / tile_m) + 3.0 * floor(q.y / tile_m), 4.0)) * 48, int(bed_row) * 48);
	vec3 bed = texelFetch(bed_atlas, var_ + tp, 0).rgb;
	bed = mix(bed, ramp[5], 0.38);
	if (bed_a > 0.02 && dith < bed_a * 0.95) {
		col = bed;
		// the same wave lines are visible over the sand, softly
		col = mix(col, ramp[6], shade_up * 0.45);
	}
	// shore foam: a bright rim, a retreating wave line, a faint outer swash
	float s = d + 0.16 * sin(t * 1.3 + n1 * 9.0) + (n3 - 0.5) * 0.28;
	float rim = step(s, 0.30) * step(-1.0, d);
	float swash = step(abs(s - (0.95 + 0.33 * sin(t * 0.9 + n2 * 5.0))), 0.07) * step(0.35, n3);
	float swash2 = step(abs(s - (2.1 + 0.5 * sin(t * 0.7 + 1.5 + n1 * 6.0))), 0.05) * step(0.55, n3 + n2 * 0.2) * step(d, 5.0);
	col = mix(col, foam[1], swash2 * 0.9);
	col = mix(col, foam[2], swash);
	col = mix(col, foam[3], rim);
	// the ship: foam hugging the hull outline, a bow splash and a wake that widens astern
	vec2 rel = q - ship_pos;
	vec2 side = vec2(-ship_fwd.y, ship_fwd.x);
	float a = dot(rel, ship_fwd);
	float b = dot(rel, side);
	float rr = a / ship_half.x;
	float wh = a > 0.0 ? ship_half.y * sqrt(max(1.0 - pow(abs(rr), 1.6), 0.0)) : ship_half.y * 0.97 - 1.1 * pow(abs(rr), 4.0);
	float sf = clamp(ship_speed, 0.0, 1.0);
	float out_d = abs(b) - 0.64 * wh;                                   // distance outside the hull outline
	float along = step(abs(a), ship_half.x + 0.5);
	float jitter = (n3 - 0.5) * 0.3;
	float hull_rim = along * step(0.0, out_d + 0.05) * step(out_d, 0.28 + jitter + 0.22 * sf * smoothstep(0.0, ship_half.x, a));
	float hull_band = along * step(0.28, out_d) * step(out_d, 0.8 + jitter + 0.5 * sf) * step(0.42, n3 + n2 * 0.3);
	float tip = length(rel - ship_fwd * (ship_half.x * 0.9));
	float bow = step(tip, 1.0 + 0.9 * sf) * step(0.45, n3 + 0.15);
	float k = -a - 0.78 * ship_half.x;
	float wk_w = 0.9 + 0.17 * max(k, 0.0);
	float in_wake = step(0.0, k) * step(k, 26.0) * sf;
	float wake_edge = step(abs(abs(b) - wk_w), 0.33) * step(0.28 + k * 0.012, n3 + 0.12 + n2 * 0.25);
	float wake_core = step(abs(b), wk_w * 0.55) * step(0.5 + k * 0.022, n3 * 0.9 + n2 * 0.25);
	float wake_cross = step(abs(b), wk_w) * step(fract((k - t * 2.2 * sf) * 0.45), 0.10) * step(0.62, n2) * step(0.5, n3);
	col = mix(col, foam[1], clamp(in_wake * (wake_edge + wake_core * 0.8 + wake_cross * 0.7), 0.0, 1.0));
	col = mix(col, foam[2], clamp(hull_band + bow * sf, 0.0, 1.0));
	col = mix(col, foam[3], hull_rim);
	// distance haze (only the far edge of the screen: the sea is seen from ~48 degrees, so this is subtle)
	float dist = length(wpos - CAMERA_POSITION_WORLD);
	col = mix(col, fog_colour, fog_amount * smoothstep(40.0, 110.0, dist));
	ALBEDO = col * light_tint;
}
