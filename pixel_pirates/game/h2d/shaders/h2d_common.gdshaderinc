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

const float FOG_START = 190.0;         // roughly the camera distance to the ship

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
float h2d_cloud_shadow(vec2 xz) {
	float n = h2d_fbm(xz * 0.0075 - h2d_wind_to * h2d_time * 2.2);
	float cover = smoothstep(0.55 - 0.35 * h2d_cloud, 0.75 - 0.2 * h2d_cloud, n);
	return 1.0 - 0.38 * cover * h2d_cloud;
}

vec3 h2d_fog_mix(vec3 c, float dist) {
	float f = 1.0 - exp(-h2d_fog_density * max(dist - FOG_START, 0.0));
	return mix(c, h2d_fog_col, clamp(f, 0.0, 1.0));
}

vec3 h2d_out(vec3 c) {
	return pow(clamp(c * h2d_exposure, vec3(0.0), vec3(1.0)), vec3(h2d_gamma));
}
