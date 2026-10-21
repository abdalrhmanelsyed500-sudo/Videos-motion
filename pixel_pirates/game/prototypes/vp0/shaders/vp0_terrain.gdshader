// VP-0 terrain: ONE plane for the whole ground of a scene. A 1 m cell map (R8: ground type = row of the tile atlas, 255 = water) and a tile atlas
// (48 px = 2 m, 4 variants per row). The cell lookup is displaced by noise, so the borders between grass, sand, cobble and dirt are
// organic pixel edges instead of a straight 1 m grid. Texels are snapped to the 24 px/m art grid. Cost: 1 + 4 cell fetches, 1 atlas fetch, 1 noise fetch.
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_disabled;

uniform sampler2D cells : filter_nearest, repeat_disable;
uniform sampler2D atlas : filter_nearest, repeat_disable;
uniform float tile_m = 2.0;
uniform sampler2D noise_tex : filter_linear, repeat_enable;
uniform vec2 origin = vec2(-30.0, -17.0);
uniform ivec2 cell_count = ivec2(60, 34);
uniform float ppm = 24.0;
uniform vec3 light_tint = vec3(1.0);
uniform vec3 edge_colour = vec3(0.15, 0.21, 0.12);
uniform float wobble = 0.85;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

int type_at(vec2 p) {
	ivec2 c = ivec2(floor(p - origin));
	c = clamp(c, ivec2(0), cell_count - ivec2(1));      // the map edge continues outward (grass to the north, water to the south)
	return int(texelFetch(cells, c, 0).r * 255.0 + 0.5);
}

void fragment() {
	vec2 q = (floor(wpos.xz * ppm) + 0.5) / ppm;
	vec2 disp = (texture(noise_tex, q * 0.32).rg - 0.5) * wobble;
	vec2 p = q + disp;
	int t = type_at(p);
	if (t == 255) discard;
	vec2 tuv = fract(q / tile_m);
	ivec2 tp = ivec2(floor(tuv * 48.0));
	int var_ = int(mod(floor(p.x / tile_m) * 3.0 + floor(p.y / tile_m) * 7.0, 4.0));
	vec3 col = texelFetch(atlas, ivec2(var_ * 48, t * 48) + tp, 0).rgb;
	// grass / cobble borders: a 1 px darker line where the neighbour (3 px away) is another ground type
	float px = 3.0 / ppm;
	int t1 = type_at(p + vec2(px, 0.0));
	int t2 = type_at(p - vec2(px, 0.0));
	int t3 = type_at(p + vec2(0.0, px));
	int t4 = type_at(p - vec2(0.0, px));
	bool border = (t1 != t) || (t2 != t) || (t3 != t) || (t4 != t);
	if (border && (t == 2 || t == 3)) col = mix(col, edge_colour, 0.55);
	if (border && (t == 4 || t == 5)) col *= 0.82;
	ALBEDO = col * light_tint;
}
