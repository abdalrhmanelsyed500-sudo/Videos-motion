// VP-0 post: the "look". One full-screen pass over the 640x360 scene upscaled to the window.
//  - crisp NEAREST pixels in the focus band, soft linear blur toward the top and bottom (the tilt-shift of the references)
//  - thresholded bloom of the brightest pixels (lanterns, sun glints, foam), warm tinted
//  - vignette with a warm-dark hue, saturation / contrast, lifted purple shadows (never pure black)
// Profile: taps = 0 disables blur+bloom (Dev-Lite: vignette and grade only, 1 texture fetch).
shader_type canvas_item;

uniform sampler2D src_near : filter_nearest;
uniform sampler2D src_lin : filter_linear;
uniform float focus_y = 0.55;
uniform float focus_half = 0.14;
uniform float ramp_w = 0.34;
uniform float max_blur_px = 7.0;
uniform int taps = 8;
uniform float bloom = 0.35;
uniform float bloom_threshold = 0.62;
uniform float bloom_radius_px = 7.0;
uniform vec3 bloom_tint = vec3(1.0, 0.82, 0.6);
uniform float vignette = 0.62;
uniform vec3 vignette_colour = vec3(0.10, 0.05, 0.10);
uniform float saturation = 1.12;
uniform float contrast = 1.07;
uniform float shadow_lift = 0.035;
uniform vec3 lift_colour = vec3(0.16, 0.09, 0.13);
uniform vec3 grade_mul = vec3(1.0);
uniform float fade = 1.0;

float lum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

void fragment() {
	vec2 uv = UV;
	vec2 px = 1.0 / vec2(textureSize(src_lin, 0)) ;
	float dy = abs(uv.y - focus_y);
	float blur = smoothstep(focus_half, focus_half + ramp_w, dy);
	vec3 col = texture(src_near, uv).rgb;
	if (taps > 0) {
		float rad = blur * max_blur_px;                   // in OUTPUT pixels: converted below through the output size
		vec2 opx = SCREEN_PIXEL_SIZE;
		vec3 acc = col;
		float wsum = 1.0;
		if (rad > 0.4) {
			for (int i = 0; i < 12; i++) {
				if (i >= taps) break;
				float a = float(i) * 2.399963 ;
				float r = (0.35 + 0.65 * sqrt((float(i) + 0.5) / float(taps))) * rad;
				vec2 o = vec2(cos(a), sin(a)) * r * opx;
				acc += texture(src_lin, uv + o).rgb;
				wsum += 1.0;
			}
			vec3 bl = acc / wsum;
			col = mix(col, bl, clamp(blur * 1.6, 0.0, 1.0));
		}
		if (bloom > 0.0) {
			vec3 b = vec3(0.0);
			vec2 opx2 = SCREEN_PIXEL_SIZE * bloom_radius_px;
			for (int j = 0; j < 8; j++) {
				float a = float(j) * 0.785398;
				vec3 s = texture(src_lin, uv + vec2(cos(a), sin(a)) * opx2).rgb;
				b += max(s - vec3(bloom_threshold), vec3(0.0));
				vec3 s2 = texture(src_lin, uv + vec2(cos(a + 0.39), sin(a + 0.39)) * opx2 * 2.0).rgb;
				b += max(s2 - vec3(bloom_threshold), vec3(0.0)) * 0.6;
			}
			col += b * (bloom / 8.0) * bloom_tint;
		}
	}
	// grade
	col *= grade_mul;
	float l = lum(col);
	col = mix(vec3(l), col, saturation);
	col = (col - 0.5) * contrast + 0.5;
	col = mix(col, lift_colour + col * 0.85, shadow_lift * pow(1.0 - clamp(l, 0.0, 1.0), 3.0) * 6.0);
	vec2 c = uv - vec2(0.5);
	float v = smoothstep(0.30, 0.82, length(c * vec2(1.0, 1.15)));
	col = mix(col, vignette_colour, v * vignette);
	col = clamp(col, vec3(0.035, 0.03, 0.05), vec3(0.985, 0.97, 0.95));
	COLOR = vec4(col * fade, 1.0);
}
