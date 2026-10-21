// CP-2 Release A ship deck: the whole interior and deck of the sloop as a few merged meshes (ship_mesh.gd), painted per pixel
// with planks, staves, canvas, rope and fish so no texture is needed. Lit by the ONE sun of every H2D shader plus up to four
// lanterns (a cheap distance falloff, no real-time lights). Cheap on purpose: no transparency (dissolve = dither + discard),
// no extra passes. Vertex colour = tint, alpha < 0.9 = "see-through" geometry that dissolves in a hole around the pirate.
// UV.x = material id (see ship_mesh.gd), UV.y = height up the object (0..1). NOT YET RUN ON THE USER'S PC.
// VP-1A: deck planks, hull strakes, timber and sailcloth now come from ONE 256x256 atlas (art/vp1/ship_mats.png, tools/vp1/make_ship_mats.py),
// sampled nearest at the deck's art-pixel density; sails are lit from both sides (translucent canvas); depth-jump outlines and a salt/wet
// pass tie the meshes to the outlined sprites (hero, island).
// VP-1A.2 LIGHTING: the sun now casts REAL (analytic) shadows on the deck and props: each fragment shoots one ray towards the sun against
// a short list of boxes (mast, cabin, nest, barrels, crates, cannons, winch, helm, the pirate), the two sails (translucent: they only half
// darken), and the bulwark (read from the hull outline). Contact darkening (AO) comes from the same list. Lanterns are real light sources
// with a normal term, warm falloff and a flicker; iron and brass catch a small sun glint. No render pass, no shadow map, no transparency.
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

uniform float texel = 0.0694;          // one art pixel in ship metres (1 / (3.6 px per m * zoom 4))
uniform float interior = 0.0;          // 0 open air .. 1 below deck / inside the cabin: sun mostly gone, lanterns carry the light
uniform float fade = 1.0;              // 1 solid .. 0 gone, dithered (cabin roof, crossfade with the sailing sprite)
uniform float see_r = 0.15;            // radius of the hole around the pirate, in screen heights
uniform vec2 hero_uv = vec2(-1.0, -1.0);
uniform float hero_dist = 0.0;         // camera distance of the pirate: only geometry NEARER than this dissolves
uniform float hero_y = 99.0;           // VP-1A.2: only geometry BELOW this height dissolves around the pirate (rails, cabin roof), never the sails or rigging above his head
uniform float aspect = 1.7778;
uniform float lamp_day = 0.0;          // 0: lanterns glow only at night, 1: always on (below deck)
uniform vec4 lampA = vec4(0.0, 0.0, 0.0, 0.0);   // model-space x, y, z of the lantern, w = strength
uniform vec4 lampB = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec4 lampC = vec4(0.0, 0.0, 0.0, 0.0);
uniform vec4 lampD = vec4(0.0, 0.0, 0.0, 0.0);
uniform float lamp_r = 6.5;
uniform vec3 lamp_col = vec3(1.0, 0.68, 0.32);
uniform float wet = 0.0;
uniform sampler2D mats : filter_nearest, repeat_disable;   // VP-1A material atlas: R value, G warm/cool, B crevice
uniform float tex_on = 1.0;           // 0: the old procedural patterns only (fallback if the atlas is missing)
uniform float outline = 1.0;          // 0 off (Dev-Lite may turn it off), 1 on
uniform float outline_k = 0.55;       // how dark the outline pixel is
uniform float tile_m = 8.889;
// VP-1A.2 shadows (model space: x starboard, y up, -z bow). Set by ship_deck_view.gd; sh_n = 0 switches everything off (interiors).
uniform vec4 sh_c[40];                 // box centres
uniform vec4 sh_h[40];                 // box half extents
uniform int sh_n = 0;                  // how many boxes are live (Low-End uses fewer)
uniform vec4 sailA = vec4(0.0);        // mainsail triangle (model space), w = how much it darkens (0 = no sail)
uniform vec4 sailB = vec4(0.0);
uniform vec4 sailC = vec4(0.0);
uniform vec4 jibA = vec4(0.0);
uniform vec4 jibB = vec4(0.0);
uniform vec4 jibC = vec4(0.0);
uniform vec4 hero_m = vec4(0.0);       // the pirate's feet in model space, w = 1 when on this deck
uniform float bulwark_y = 2.15;        // top of the bulwark (model height); 0 = no bulwark shadow
uniform float shadow_soft = 0.035;     // dithered penumbra: how far the sun ray is jittered
uniform float shadow_max = 12.0;       // longest shadow ray, metres
uniform float ao_amt = 0.4;            // contact darkening strength         // one atlas tile in ship metres (128 px at 14.4 px/m)

varying vec3 l_pos;
varying vec3 l_nrm;
varying vec3 w_nrm;
varying vec3 w_pos;
varying vec4 v_col;
varying float v_mat;
varying float v_rel;
varying vec3 sun_m;

void vertex() {
	l_pos = VERTEX;
	l_nrm = NORMAL;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	v_col = COLOR;
	v_mat = UV.x;
	v_rel = UV.y;
	sun_m = normalize(transpose(mat3(MODEL_MATRIX)) * h2d_sun_dir);
}

float ign(vec2 p) {
	return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

float q_hash(vec2 q) {
	return h2d_hash(q * 0.137 + 3.1);
}

float lamp_term(vec4 l, vec3 p, vec3 nm) {
	if (l.w <= 0.0) {
		return 0.0;
	}
	vec3 dv = l.xyz - p;
	float d = length(dv) / lamp_r;
	float k = clamp(1.0 - d, 0.0, 1.0);
	float face = 0.3 + 0.7 * clamp(dot(nm, normalize(dv)), 0.0, 1.0);
	return k * k * l.w * face;
}

// One tile of the material atlas: idx 0 deck, 1 hull, 2 timber, 3 canvas. c in ship metres; returns (value, warm, crevice).
vec3 mat_tile(int idx, vec2 c) {
	vec2 f = fract(c / tile_m);
	f = clamp(f, vec2(0.002), vec2(0.998));
	vec2 o = vec2(float(idx % 2), float(idx / 2));
	return texture(mats, (o + f) * 0.5).rgb;
}

// walkable hull half-width at u (the same table as ship_layout.gd HULL[0]); the bulwark stands on its outer 0.3 m
float hull_hw(float u) {
	const float us[9] = float[9](-11.0, -10.0, -8.0, -3.0, 2.0, 5.0, 7.5, 9.5, 11.0);
	const float hs[9] = float[9](1.9, 2.6, 3.0, 3.1, 3.05, 2.7, 1.9, 0.9, 0.15);
	if (u <= us[0] || u >= us[8]) {
		return -1.0;
	}
	float r = hs[0];
	for (int i = 0; i < 8; i++) {
		if (u <= us[i + 1]) {
			r = mix(hs[i], hs[i + 1], (u - us[i]) / (us[i + 1] - us[i]));
			break;
		}
	}
	return r;
}

float box_hit(vec3 o, vec3 il, vec3 c, vec3 h) {
	vec3 t1 = (c - h - o) * il;
	vec3 t2 = (c + h - o) * il;
	vec3 tn = min(t1, t2);
	vec3 tf = max(t1, t2);
	float t_in = max(max(tn.x, tn.y), tn.z);
	float t_out = min(min(tf.x, tf.y), tf.z);
	return (t_out > t_in && t_in > 0.03 && t_in < shadow_max) ? 1.0 : 0.0;
}

float tri_hit(vec3 o, vec3 d, vec3 a, vec3 b, vec3 c) {
	vec3 e1 = b - a;
	vec3 e2 = c - a;
	vec3 pv = cross(d, e2);
	float det = dot(e1, pv);
	if (abs(det) < 0.000001) {
		return 0.0;
	}
	float inv = 1.0 / det;
	vec3 tv = o - a;
	float u = dot(tv, pv) * inv;
	if (u < 0.0 || u > 1.0) {
		return 0.0;
	}
	vec3 qv = cross(tv, e1);
	float v = dot(d, qv) * inv;
	if (v < 0.0 || u + v > 1.0) {
		return 0.0;
	}
	float t = dot(e2, qv) * inv;
	return (t > 0.03 && t < shadow_max) ? 1.0 : 0.0;
}

// x: hard shadow (0/1) from boxes, hero and bulwark; y: translucent shadow from the sails; z: contact darkening (0..1)
vec3 sun_shadow(vec3 p, vec3 o, vec3 Lm, bool is_cloth) {
	float hard = 0.0;
	float soft_s = 0.0;
	float ao = 0.0;
	vec3 il = 1.0 / vec3(abs(Lm.x) < 0.0001 ? 0.0001 : Lm.x, abs(Lm.y) < 0.0001 ? 0.0001 : Lm.y, abs(Lm.z) < 0.0001 ? 0.0001 : Lm.z);
	for (int i = 0; i < 40; i++) {
		if (i >= sh_n) {
			break;
		}
		vec3 c = sh_c[i].xyz;
		vec3 h = sh_h[i].xyz;
		hard = max(hard, box_hit(o, il, c, h));
		float d = length(max(abs(p - c) - h, vec3(0.0)));
		if (d > 0.03 && d < 0.5 && p.y < c.y + h.y + 0.15) {
			float k = 1.0 - d / 0.5;
			ao += k * k;
		}
	}
	if (hero_m.w > 0.5) {
		hard = max(hard, box_hit(o, il, hero_m.xyz + vec3(0.0, 0.8, 0.0), vec3(0.2, 0.8, 0.2)));
	}
	if (bulwark_y > 0.0) {
		for (int k = 1; k < 9; k++) {
			vec3 q = o + Lm * (float(k) * 0.2);
			if (q.y > bulwark_y) {
				break;
			}
			float hw = hull_hw(-q.z);
			if (hw > 0.0 && abs(q.x) > hw - 0.3 && abs(q.x) < hw + 0.05) {
				hard = 1.0;
				break;
			}
		}
	}
	if (!is_cloth) {
		if (sailA.w > 0.0) {
			soft_s = max(soft_s, tri_hit(o, Lm, sailA.xyz, sailB.xyz, sailC.xyz) * sailA.w);
		}
	}
	if (jibA.w > 0.0) {
		soft_s = max(soft_s, tri_hit(o, Lm, jibA.xyz, jibB.xyz, jibC.xyz) * jibA.w);
	}
	return vec3(hard, soft_s, clamp(ao, 0.0, 1.0));
}

void fragment() {
	if (fade < 0.999 && ign(FRAGCOORD.xy + vec2(1.7, 4.1)) > fade) {
		discard;
	}
	if (v_col.a < 0.9 && hero_uv.x >= 0.0) {
		float dist = length(CAMERA_POSITION_WORLD - w_pos);
		if (dist < hero_dist - 0.4 && w_pos.y < hero_y) {
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
		if (tex_on > 0.5) {
			vec3 tx = mat_tile(0, vec2(l_pos.x, -l_pos.z));
			pal = tint * (2.0 * tx.r) * (0.92 + 0.16 * ph);
			pal = mix(pal, pal * vec3(1.10, 1.0, 0.86), clamp(tx.g - 0.5, 0.0, 0.5) * 1.6);
			pal = mix(pal, pal * vec3(0.90, 0.98, 1.08), clamp(0.5 - tx.g, 0.0, 0.5) * 1.6);
			pal *= 1.0 - 0.18 * tx.b * wet;
		} else {
			pal = tint * (0.86 + 0.26 * ph) * (0.94 + 0.12 * h);
			if (fract(l_pos.x / pw) < 0.07) {
				pal = tint * 0.45;
			}
			float joint = fract((l_pos.z + ph * 4.0) / 2.6);
			if (joint < 0.025) {
				pal = tint * 0.5;
			}
		}
	} else if (m == 1) {                             // hull boards, horizontal
		if (tex_on > 0.5) {
			vec3 tx = mat_tile(1, vec2(c.x * 0.7 + c.y * 0.0, -c.y));
			pal = tint * (2.0 * tx.r);
			pal = mix(pal, pal * vec3(1.12, 1.0, 0.84), clamp(tx.g - 0.5, 0.0, 0.5) * 1.4);
			pal = mix(pal, pal * vec3(0.88, 0.98, 1.1), clamp(0.5 - tx.g, 0.0, 0.5) * 1.4);
		} else {
			float bh = 0.30;
			pal = tint * (0.9 + 0.2 * h);
			if (fract(c.y / bh) < 0.1) {
				pal = tint * 0.5;
			}
			float bi = floor(c.y / bh);
			pal *= 0.92 + 0.16 * h2d_hash(vec2(bi, 3.0));
		}
	} else if (m == 2) {                             // timber: beams, posts, spars
		if (tex_on > 0.5) {
			vec3 tx = mat_tile(2, c * 1.0);
			pal = tint * (2.0 * tx.r) * (0.9 + 0.2 * h);
		} else {
			pal = tint * (0.82 + 0.3 * h2d_noise(vec2(q.x * 0.3 + q.y * 0.04, q.y * 0.9 + q.x * 0.05)));
		}
	} else if (m == 3) {                             // barrel: staves (angle round the lathe), grain, iron hoops
		float fr = v_mat - 3.0;
		if (fr > 0.02) {
			float stv = (fr - 0.05) * 2.857 * 14.0;
			float si = floor(stv);
			float sf = fract(stv);
			float sh = h2d_hash(vec2(si, 5.0));
			pal = tint * (0.78 + 0.34 * sh) * (0.94 + 0.1 * h);
			if (tex_on > 0.5) {
				pal *= 2.0 * mat_tile(2, vec2(si * 0.37, l_pos.y * 1.7 + sh * 3.0)).r;
			}
			if (sf < 0.1 || sf > 0.94) {
				pal = tint * 0.5;
			}
			pal *= 0.94 + 0.1 * smoothstep(0.1, 0.5, sf);   // each stave is a little rounder in the middle
		} else {
			float stave = fract(c.x / 0.15);
			pal = tint * (0.85 + 0.25 * h) * (stave < 0.12 ? 0.62 : 1.0);
		}
		float hp = v_rel;
		if (abs(hp - 0.12) < 0.05 || abs(hp - 0.86) < 0.05 || abs(hp - 0.5) < 0.032 || abs(hp - 0.3) < 0.02 || abs(hp - 0.7) < 0.02) {
			pal = vec3(0.19, 0.18, 0.18) * (0.8 + 0.4 * h);
			if (fract(l_pos.x * 7.0 + l_pos.z * 5.0) > 0.86) {
				pal = vec3(0.45, 0.42, 0.36);   // a rivet
			}
		}
	} else if (m == 4) {                             // canvas: panels, stitching, patches, reef bands (atlas) + weave
		if (tex_on > 0.5) {
			vec3 tx = mat_tile(3, vec2(l_pos.z * 0.9 + l_pos.x * 0.35, -l_pos.y * 0.9));
			pal = tint * (2.0 * tx.r) * (0.96 + 0.08 * h);
			pal = mix(pal, pal * vec3(1.10, 0.97, 0.80), clamp(tx.g - 0.5, 0.0, 0.5) * 1.5);
		} else {
			float weave = mod(q.x + q.y, 2.0) < 1.0 ? 1.0 : 0.94;
			pal = tint * weave * (0.92 + 0.1 * h);
			if (fract((l_pos.x + l_pos.z * 0.7) / 0.9) < 0.035) {
				pal = tint * 0.72;
			}
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
		if (tex_on > 0.5) {
			pal *= 2.0 * mat_tile(2, c * 1.3 + 3.0).r;
		}
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
	} else if (m == 14) {                            // fishing net: a diamond lattice of twine, the holes are discarded
		float kk = 3.2;
		vec2 dd = vec2(fract((l_pos.x + l_pos.z) * kk + l_pos.y * kk * 0.6), fract((l_pos.x - l_pos.z) * kk - l_pos.y * kk * 0.6));
		float ln = min(min(dd.x, 1.0 - dd.x), min(dd.y, 1.0 - dd.y));
		if (ln > 0.2) {
			discard;
		}
		pal = tint * (0.85 + 0.3 * h);
	} else if (m == 13) {                            // void: the hatch opening, the dark under the deck
		pal = tint * (0.8 + 0.3 * h);
	}
	// light: one sun (with shadows), a cool ambient (with contact darkening) and the lanterns
	vec3 n = normalize(w_nrm);
	float sd0 = dot(n, h2d_sun_dir);
	float ndl = clamp(sd0, 0.0, 1.0);
	float cloth = 0.0;
	if (m == 4) {                                    // sailcloth is translucent: lit from both faces, a little brighter when the sun is behind it
		ndl = clamp(abs(sd0) * 0.8 + 0.18, 0.0, 1.0);
		cloth = clamp(-sd0, 0.0, 1.0);
	}
	ndl = mix(floor(ndl * 4.0 + 0.5) / 4.0, ndl, 0.35);
	float sun_k = mix(1.0, 0.12, interior);
	float vis = 1.0;
	float ao = 0.0;
	float sail_sh = 0.0;
	if (sh_n > 0 && interior < 0.5 && h2d_sun_dir.y > 0.05) {
		vec3 nm = normalize(l_nrm);
		vec3 o = l_pos + nm * (sd0 >= 0.0 ? 0.05 : -0.05);
		float jx = ign(FRAGCOORD.xy + vec2(3.3, 1.1)) - 0.5;
		float jy = ign(FRAGCOORD.yx + vec2(9.7, 5.3)) - 0.5;
		vec3 Lj = normalize(sun_m + vec3(jx, jy, jx * jy * 2.0) * shadow_soft);
		vec3 sh3 = sun_shadow(l_pos, o, Lj, m == 4);
		vis = 1.0 - sh3.x;
		sail_sh = sh3.y;
		ao = sh3.z;
	}
	vec3 sun_c = h2d_sun_col * ndl * sun_k * vis;
	// light that went through a sail is dimmer and warmer
	sun_c = mix(sun_c, sun_c * vec3(0.62, 0.52, 0.42), sail_sh * (1.0 - interior));
	vec3 amb = h2d_amb_col * mix(1.0, 0.62, interior) * (0.78 + 0.22 * n.y);
	// bounce / sky fill: the shadow side is cool and never black (the deck wood and the sea throw light back into it)
	amb += (h2d_sun_col * 0.16 * sun_k + vec3(-0.01, 0.015, 0.05)) * (1.0 - interior) * (0.5 + 0.5 * n.y);
	amb *= 1.0 - clamp(ao, 0.0, 0.6) * ao_amt;
	vec3 col = pal * (amb + sun_c) * (1.0 - 0.18 * clamp(ao, 0.0, 0.6));
	col *= 1.0 - 0.2 * h2d_rain * (1.0 - interior);
	float lamp = lamp_term(lampA, l_pos, l_nrm) + lamp_term(lampB, l_pos, l_nrm) + lamp_term(lampC, l_pos, l_nrm) + lamp_term(lampD, l_pos, l_nrm);
	float lamp_on = max(lamp_day, smoothstep(0.12, 0.7, h2d_night));
	float flick = 0.94 + 0.06 * sin(h2d_time * 7.3 + l_pos.x * 0.5) * sin(h2d_time * 3.1 + 1.7);
	vec3 warm = lamp_col * lamp * lamp_on * flick;
	col += pal * warm * 1.4;
	col += pal * h2d_sun_col * cloth * 0.28 * (1.0 - interior) * (1.0 - 0.6 * sail_sh);
	// a small crisp glint on metal where the sun hits it
	if (m == 7 && vis > 0.5) {
		vec3 vw = normalize(CAMERA_POSITION_WORLD - w_pos);
		float sp = pow(max(dot(n, normalize(h2d_sun_dir + vw)), 0.0), 18.0);
		col += h2d_sun_col * step(0.55, sp) * 0.55 * (1.0 - h2d_overcast);
	}
	if (m == 12) {
		col = pal * 1.15;
	}
	col *= 1.0 - 0.18 * wet;
	if (outline > 0.5 && m != 12) {
		// outline on the FAR side of a depth jump (the near object keeps its colour), like the 1-px outlines of the sprites
		float zd = -VERTEX.z;
		float par_x = mod(floor(FRAGCOORD.x), 2.0) < 0.5 ? 1.0 : -1.0;
		float par_y = mod(floor(FRAGCOORD.y), 2.0) < 0.5 ? 1.0 : -1.0;
		float nx = par_x * dFdx(zd);
		float ny = par_y * dFdy(zd);
		float thr = 0.22 + 0.0015 * zd;
		if (nx < -thr || ny < -thr) {
			col *= outline_k;
		}
	}
	col = h2d_fog_mix(col, length(CAMERA_POSITION_WORLD - w_pos));
	ALBEDO = h2d_out(col);
}
