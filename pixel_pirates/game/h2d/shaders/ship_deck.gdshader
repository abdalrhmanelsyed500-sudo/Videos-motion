// CP-2 Release A ship deck: the whole interior and deck of the sloop as a few merged meshes (ship_mesh.gd), painted per pixel
// with planks, staves, canvas, rope and fish so no texture is needed. Lit by the ONE sun of every H2D shader plus up to four
// lanterns (a cheap distance falloff, no real-time lights). Cheap on purpose: no transparency (dissolve = dither + discard),
// no extra passes. Vertex colour = tint, alpha < 0.9 = "see-through" geometry that dissolves in a hole around the pirate.
// UV.x = material id (see ship_mesh.gd), UV.y = height up the object (0..1). NOT YET RUN ON THE USER'S PC.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform float texel = 0.0694;          // one art pixel in ship metres (1 / (3.6 px per m * zoom 4))
uniform float interior = 0.0;          // 0 open air .. 1 below deck / inside the cabin: sun mostly gone, lanterns carry the light
uniform float fade = 1.0;              // 1 solid .. 0 gone, dithered (cabin roof, crossfade with the sailing sprite)
uniform float see_r = 0.15;            // radius of the hole around the pirate, in screen heights
uniform vec2 hero_uv = vec2(-1.0, -1.0);
uniform float hero_dist = 0.0;         // camera distance of the pirate: only geometry NEARER than this dissolves
uniform float aspect = 1.7778;
uniform float lamp_day = 0.0;          // 0: lanterns glow only at night, 1: always on (below deck)
uniform vec4 lampA = vec4(0.0, 0.0, 0.0, 0.0);   // model-space x, y, z of the lantern, w = strength
uniform vec4 lampB = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec4 lampC = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec4 lampD = vec4(0.0, 0.0, 0.0, 0.0);
uniform float lamp_r = 6.5;
uniform vec3 lamp_col = vec3(1.0, 0.68, 0.32);
uniform float wet = 0.0;

varying vec3 l_pos;
varying vec3 l_nrm;
varying vec3 w_nrm;
varying vec3 w_pos;
varying vec4 v_col;
varying float v_mat;
varying float v_rel;

void vertex() {
	l_pos = VERTEX;
	l_nrm = NORMAL;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_col = COLOR;
	v_mat = UV.x;
	v_rel = UV.y;
}

float ign(vec2 p) {
	return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

float q_hash(vec2 q) {
	return h2d_hash(q * 0.137 + 3.1);
}

float lamp_term(vec4 l, vec3 p) {
	if (l.w <= 0.0) {
		return 0.0;
	}
	float d = length(p - l.xyz) / lamp_r;
	float k = clamp(1.0 - d, 0.0, 1.0);
	return k * k * l.w;
}

void fragment() {
	if (fade < 0.999 && ign(FRAGCOORD.xy + vec2(1.7, 4.1)) > fade) {
		discard;
	}
	if (v_col.a < 0.9 && hero_uv.x >= 0.0) {
		float dist = length(CAMERA_POSITION_WORLD - w_pos);
		if (dist < hero_dist - 0.4) {
			vec2 d = (SCREEN_UV - hero_uv) * vec2(aspect, 1.0);
			float k = smoothstep(see_r * 0.55, see_r, length(d));
			if (ign(FRAGCOORD.xy) > k) {
				discard;
			}
		}
	}
	// which plane the pattern lives in: floors use (x, z), walls (along, y)
	vec3 an = abs(l_nrm);
	vec2 c;
	if (an.y > 0.7) {
		c = l_pos.xz;
	} else if (an.x > an.z) {
		c = vec2(l_pos.z, l_pos.y);
	} else {
		c = vec2(l_pos.x, l_pos.y);
	}
	vec2 q = floor(c / texel);
	float h = q_hash(q);
	vec3 tint = v_col.rgb;
	vec3 pal = tint;
	int m = int(v_mat + 0.5);
	if (m == 0) {                                    // deck planks, run fore and aft (z)
		float pw = 0.34;
		float pidx = floor(l_pos.x / pw);
		float ph = h2d_hash(vec2(pidx, 7.0));
		pal = tint * (0.86 + 0.26 * ph) * (0.94 + 0.12 * h);
		if (fract(l_pos.x / pw) < 0.07) {
			pal = tint * 0.45;
		}
		float joint = fract((l_pos.z + ph * 4.0) / 2.6);
		if (joint < 0.025) {
			pal = tint * 0.5;
		}
	} else if (m == 1) {                             // hull boards, horizontal
		float bh = 0.30;
		pal = tint * (0.9 + 0.2 * h);
		if (fract(c.y / bh) < 0.1) {
			pal = tint * 0.5;
		}
		float bi = floor(c.y / bh);
		pal *= 0.92 + 0.16 * h2d_hash(vec2(bi, 3.0));
	} else if (m == 2) {                             // timber: beams, posts, spars
		pal = tint * (0.82 + 0.3 * h2d_noise(vec2(q.x * 0.3 + q.y * 0.04, q.y * 0.9 + q.x * 0.05)));
	} else if (m == 3) {                             // barrel: staves and two iron hoops
		float stave = fract(c.x / 0.15);
		pal = tint * (0.85 + 0.25 * h) * (stave < 0.12 ? 0.62 : 1.0);
		float hp = v_rel;
		if (abs(hp - 0.12) < 0.045 || abs(hp - 0.86) < 0.045 || abs(hp - 0.5) < 0.03) {
			pal = vec3(0.17, 0.16, 0.16) * (0.8 + 0.4 * h);
		}
	} else if (m == 4) {                             // canvas: weave, panel seams
		float weave = mod(q.x + q.y, 2.0) < 1.0 ? 1.0 : 0.94;
		pal = tint * weave * (0.92 + 0.1 * h);
		if (fract((l_pos.x + l_pos.z * 0.7) / 0.9) < 0.035) {
			pal = tint * 0.72;
		}
	} else if (m == 5) {                             // rope: a diagonal twist
		float tw = fract((l_pos.x + l_pos.y + l_pos.z) * 9.0);
		pal = tint * (tw < 0.5 ? 1.0 : 0.72);
	} else if (m == 6) {                             // fish: silver scales, dark backs, a red gill here and there
		float row = mod(q.y, 6.0);
		float sc = mod(q.x + (mod(floor(q.y / 2.0), 2.0)) * 1.0, 3.0);
		pal = vec3(0.66, 0.76, 0.85) * (0.82 + 0.3 * h);
		if (sc < 1.0) {
			pal *= 0.86;
		}
		if (row < 1.0) {
			pal = vec3(0.20, 0.30, 0.42) * (0.8 + 0.4 * h);
		}
		if (h > 0.965) {
			pal = vec3(0.78, 0.20, 0.16);
		}
		if (h < 0.035) {
			pal = vec3(0.05, 0.06, 0.08);
		}
		pal = mix(pal, tint, 0.15);
	} else if (m == 7) {                             // iron
		pal = tint * (0.8 + 0.4 * h) * (h > 0.93 ? 1.6 : 1.0);
	} else if (m == 8) {                             // painted wood: a little noise
		pal = tint * (0.93 + 0.14 * h);
	} else if (m == 9) {                             // crate boards, vertical, with a dark frame
		float bw = 0.2;
		pal = tint * (0.88 + 0.22 * h2d_hash(vec2(floor(c.x / bw), 11.0)));
		if (fract(c.x / bw) < 0.1) {
			pal = tint * 0.5;
		}
		if (v_rel < 0.1 || v_rel > 0.9) {
			pal = tint * 0.6;
		}
	} else if (m == 10) {                            // sack: lumpy cloth, a rope tie near the top
		pal = tint * (0.75 + 0.35 * h2d_noise(c * 7.0 + 4.0)) * (0.94 + 0.1 * h);
		if (abs(v_rel - 0.78) < 0.05) {
			pal = vec3(0.45, 0.32, 0.18);
		}
	} else if (m == 11) {                            // hammock cloth, coarse weave
		pal = tint * (mod(q.x + q.y, 3.0) < 1.0 ? 0.9 : 1.0) * (0.92 + 0.12 * h);
	} else if (m == 12) {                            // lantern: glows by itself
		pal = tint * 1.3;
	} else if (m == 13) {                            // void: the hatch opening, the dark under the deck
		pal = tint * (0.8 + 0.3 * h);
	}
	// light: one sun, quantised like the sprites, plus the ambient and the lanterns
	vec3 n = normalize(w_nrm);
	float ndl = clamp(dot(n, h2d_sun_dir), 0.0, 1.0);
	ndl = mix(floor(ndl * 4.0 + 0.5) / 4.0, ndl, 0.35);
	float sun_k = mix(1.0, 0.12, interior);
	vec3 amb = h2d_amb_col * mix(1.0, 0.62, interior) * (0.78 + 0.22 * n.y);
	vec3 col = pal * (amb + h2d_sun_col * ndl * sun_k);
	col *= 1.0 - 0.2 * h2d_rain * (1.0 - interior);
	float lamp = lamp_term(lampA, l_pos) + lamp_term(lampB, l_pos) + lamp_term(lampC, l_pos) + lamp_term(lampD, l_pos);
	float lamp_on = max(lamp_day, h2d_night);
	col += pal * lamp_col * lamp * lamp_on * (0.5 + 0.5 * clamp(ndl + 0.5, 0.0, 1.0)) * 1.5;
	if (m == 12) {
		col = pal;
	}
	col *= 1.0 - 0.18 * wet;
	col = h2d_fog_mix(col, length(CAMERA_POSITION_WORLD - w_pos));
	ALBEDO = h2d_out(col);
}
