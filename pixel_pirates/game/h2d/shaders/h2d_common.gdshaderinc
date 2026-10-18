// Shared by every H2D-0 shader: one sun, one ambient colour, one fog, one output transfer.
// The global uniforms are registered and updated every frame by h2d/sea_view_3d.gd.
global uniform vec3 h2d_sun_dir;       // unit vector TO the sun (x east, y up, z south)
global uniform vec3 h2d_sun_col;       // key light colour x strength
global uniform vec3 h2d_amb_col;       // ambient colour
global uniform vec3 h2d_fog_col;
global uniform float h2d_fog_density;  // per scene metre, beyond FOG_START
global uniform float h2d_gamma;        // 2.2 when the renderer encodes sRGB on output, 1.0 when it does not (auto-calibrated)
global uniform float h2d_exposure;
global uniform float h2d_time;         // real seconds
global uniform vec2 h2d_wind_to;       // unit vector the wind blows TOWARDS (x east, y south)
global uniform float h2d_cloud;
global uniform float h2d_storm;
global uniform float h2d_rain;
global uniform vec2 h2d_adv;           // metres the wind has carried the air since the start: rain cells, gust patches, ripples drift with it
global uniform float h2d_wind_ms;      // wind speed now, gust included, in m/s
global uniform float h2d_gust;         // 0..1 gust strength now
global uniform float h2d_sea;          // 0..1 sea-state index (calm .. storm), from the shared environment model
global uniform float h2d_overcast;     // 0 open sky .. 1 full overcast (rain, storm, fog): no cloud shadows, no sun glints, flat light
global uniform float h2d_fog_start;    // scene metres from the camera where the fog begins (closer in thick fog)
global uniform vec2 h2d_focus;         // the ship's position: the gust patch is always over it while a gust blows
global uniform float h2d_rain_dens;    // share of the rain slots that are active at full rain (set by the effects budget, so every level looks alike)

// The wave field (h2d/env_model.gd -> wave_model.gd build()): four waves [dir_x, dir_z, k, amplitude] and the crest shape
// (x = exponent p, y = mean correction). Per-material uniforms, set from the same numbers for every shader that needs them.
uniform vec4 w0;
uniform vec4 w1;
uniform vec4 w2;
uniform vec4 w3;
uniform vec2 crest_pb = vec2(1.0, 0.0);

float h2d_hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float h2d_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = h2d_hash(i);
	float b = h2d_hash(i + vec2(1.0, 0.0));
	float c = h2d_hash(i + vec2(0.0, 1.0));
	float d = h2d_hash(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float h2d_fbm(vec2 p) {
	float s = 0.0;
	float a = 0.5;
	for (int i = 0; i < 3; i++) {
		s += a * h2d_noise(p);
		p = p * 2.03 + vec2(17.1, 9.2);
		a *= 0.5;
	}
	return s;
}

// Drifting cloud shadow: 1.0 = open sun, lower = under cloud. Cheap, and the best "this sea is huge" cue.
// Under an overcast sky the light is flat, so the shadows fade out with it.
float h2d_cloud_shadow(vec2 xz) {
	float n = h2d_fbm(xz * 0.0075 - h2d_wind_to * h2d_time * 2.2);
	float cover = smoothstep(0.55 - 0.35 * h2d_cloud, 0.75 - 0.2 * h2d_cloud, n);
	return 1.0 - 0.38 * cover * h2d_cloud * (1.0 - h2d_overcast);
}

// The gust patch (0..1): a darker, rougher area that drifts downwind with the air. It is always over the ship while a gust
// blows. The ocean darkens and roughens inside it and the rain bends inside it: they read the same field.
float h2d_gust_field(vec2 xz) {
	if (h2d_gust < 0.02) {
		return 0.0;
	}
	float thr = mix(0.80, 0.45, h2d_gust) - 0.25 * (1.0 - smoothstep(10.0, 70.0, length(xz - h2d_focus)));
	return smoothstep(thr, thr + 0.22, h2d_noise(xz * 0.02 - h2d_adv * 0.02)) * h2d_gust;
}

vec3 h2d_fog_mix(vec3 c, float dist) {
	float f = 1.0 - exp(-h2d_fog_density * max(dist - h2d_fog_start, 0.0));
	return mix(c, h2d_fog_col, clamp(f, 0.0, 1.0));
}

// ---- waves: the same function as wave_model.gd height_b(), plus the slope for shading ------------------------------
void h2d_wave_add(vec4 w, vec2 p, inout float h, inout vec2 d) {
	float k = w.z;
	float ph = k * dot(w.xy, p) - sqrt(9.81 * k) * h2d_time;
	float q = max(0.5 + 0.5 * cos(ph), 0.0001);
	h += w.w * (2.0 * pow(q, crest_pb.x) - 1.0 - crest_pb.y);
	float dd = w.w * k * (-crest_pb.x * pow(q, crest_pb.x - 1.0) * sin(ph));
	d += dd * w.xy;
}

// x = height, yz = slope (d height / d x, d height / d z)
vec3 h2d_wave(vec2 p) {
	float h = 0.0;
	vec2 d = vec2(0.0);
	h2d_wave_add(w0, p, h, d);
	h2d_wave_add(w1, p, h, d);
	h2d_wave_add(w2, p, h, d);
	h2d_wave_add(w3, p, h, d);
	return vec3(h, d);
}

float h2d_wave_h(vec2 p) {
	return h2d_wave(p).x;
}

// ---- rain: ONE drop per (grid cell, k). The falling streak (rain.gdshader) and the splash ring on the water (ocean.gdshader)
// both read these functions, so every ring on the sea is the landing of a drop you saw fall. Every slot has its OWN period
// (1.25 .. 1.9 s), so the rain never pulses or repeats in step. -------------------------------------------------------------
const float DROP_FALL_FRAC = 0.60;     // fraction of the period spent falling; the rest is the splash
const float SPLASH_T = 0.5;            // seconds a splash (crown and ring) lasts. (1 - DROP_FALL_FRAC) * 1.25 s = 0.5 s, so it always fits.

float h2d_drop_period(vec2 cell, float k) {
	return 1.25 + 0.65 * h2d_hash(mod(cell, 1024.0) * 0.91 + k * 5.3 + 9.0);
}

// Rain is patchy when it is light (bands drift downwind with the air) and nearly uniform when it is heavy, where it
// comes in SHEETS: broad bands, a few hundred metres across, that are twice as thick as the gaps between them.
float h2d_rain_local(vec2 xz) {
	float n = h2d_noise(xz * 0.011 - h2d_adv * 0.011);
	float r = clamp((h2d_rain - 0.55 * (1.0 - n) * (1.0 - 0.9 * h2d_rain)) * 1.25, 0.0, 1.0);
	float sheet = mix(0.55, 1.25, h2d_noise(xz * 0.028 - h2d_adv * 0.028 + 71.0));
	return clamp(r * mix(1.0, sheet, smoothstep(0.45, 0.85, h2d_rain)), 0.0, 1.0);
}

// A slot lands somewhere new every cycle: the seed mixes the slot k with the cycle number.
float h2d_drop_seed(float k, float cycle) {
	return k + 3.0 * mod(cycle, 61.0);
}

vec2 h2d_drop_impact(vec2 cell, float seed, float cell_m) {
	vec2 c = mod(cell, 1024.0);
	vec2 j = vec2(h2d_hash(c + seed * 7.31), h2d_hash(c.yx * 1.7 + seed * 5.17 + 11.0));
	return (cell + mix(vec2(0.25), vec2(0.75), j)) * cell_m;
}

float h2d_drop_phase(vec2 cell, float k) {
	return h2d_hash(mod(cell, 1024.0) * 0.37 + k * 3.7 + 3.0);
}

float h2d_drop_on(vec2 cell, float seed) {
	return h2d_hash(mod(cell, 1024.0) + seed * 9.1 + 29.0);
}

// 0..1 per drop: its size, speed and brightness tier
float h2d_drop_var(vec2 cell, float seed) {
	return h2d_hash(mod(cell, 1024.0) * 1.31 + seed * 2.9 + 61.0);
}

vec3 h2d_out(vec3 c) {
	return pow(clamp(c * h2d_exposure, vec3(0.0), vec3(1.0)), vec3(h2d_gamma));
}
