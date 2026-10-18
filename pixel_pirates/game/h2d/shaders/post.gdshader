// H2D-0 post-process on the upscaled 3D picture: tilt-shift depth of field, bloom (Standard and up), colour grade and vignette. Numbers come from data/look/look_profiles.json.
// TEXTURE is the SubViewport's image, so no screen texture is needed.
// H2D-0.2: the rain streaks that used to be drawn here are gone. Rain is real drops in the 3D scene (rain.gdshader).
// H2D-0.3: the haze and lightning overlays are gone too: fog is distance fog in every 3D shader, and lightning is a boost of
// the scene's own light (light_model.gd), so weather is never a flat layer on top of the picture.
shader_type canvas_item;

uniform float focus_y = 0.55;
uniform float focus_half = 0.12;
uniform float ramp_w = 0.33;
uniform float max_blur = 6.0;       // in art-grid pixels
uniform int taps = 6;
uniform float bloom_i = 0.0;
uniform float bloom_thr = 0.65;
uniform float vign_in = 0.45;
uniform float vign_out = 1.05;
uniform float vign_str = 0.7;
uniform float sat = 1.12;
uniform float con = 1.06;
uniform float shadow_lift = 0.03;
uniform vec3 lift_col = vec3(0.165, 0.086, 0.125);
uniform vec3 tint = vec3(1.0);
uniform vec2 grid = vec2(640.0, 360.0);

void fragment() {
	vec2 uv = UV;
	vec2 px = TEXTURE_PIXEL_SIZE;
	vec3 c = texture(TEXTURE, uv).rgb;

	float d = max(abs(uv.y - focus_y) - focus_half, 0.0) / ramp_w;
	float blur = clamp(d, 0.0, 1.0) * max_blur / (px.y * grid.y);
	if (blur > 0.3) {
		vec3 acc = c;
		float wsum = 1.0;
		for (int i = 0; i < 12; i++) {
			if (i >= taps) {
				break;
			}
			float a = float(i) * 2.39996;
			float r = sqrt((float(i) + 0.5) / float(taps)) * blur;
			acc += textureLod(TEXTURE, uv + vec2(cos(a), sin(a)) * r * px, 0.0).rgb;
			wsum += 1.0;
		}
		c = acc / wsum;
	}
	if (bloom_i > 0.0) {
		vec3 b = vec3(0.0);
		for (int i = 0; i < 8; i++) {
			float a = float(i) * 0.785398;
			vec3 s = textureLod(TEXTURE, uv + vec2(cos(a), sin(a)) * 7.0 * px, 0.0).rgb;
			b += max(s - vec3(bloom_thr), vec3(0.0));
		}
		c += b * (bloom_i / 8.0) * 2.0;
	}


	float lum = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(lum), c, sat);
	c = (c - 0.5) * con + 0.5;
	c += lift_col * shadow_lift * (1.0 - lum);
	c *= tint;
	float v = smoothstep(vign_in, vign_out, length((uv - 0.5) * vec2(1.0, 0.75) * 1.6));
	c *= 1.0 - v * vign_str * 0.55;
	COLOR = vec4(clamp(c, vec3(0.0), vec3(1.0)), 1.0);
}
