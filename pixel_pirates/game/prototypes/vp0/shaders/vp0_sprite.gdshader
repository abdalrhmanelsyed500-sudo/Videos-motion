// VP-0 sprite: a camera-facing pixel sprite that is ALWAYS pixel-aligned. The pivot is projected, snapped to the art-pixel grid in view space, and
// the sprite texels are laid out 1:1 around it, so a moving camera never shimmers or scales a sprite. A small depth bias pulls the quad toward the
// camera so the part of the sprite that hangs below its pivot (the footprint) is not cut by the ground. The orthographic camera makes the bias free.
// Palette-keyed emission: the pure "fire" ramp pixels (#ffa43a, #ffe08a, #ff... r > 0.995) are self-lit and ignore the light tint, so lanterns and
// windows stay bright at night with no second texture.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_opaque;

uniform sampler2D tex : filter_nearest;
uniform vec2 size_px = vec2(32.0);
uniform vec2 pivot_px = vec2(16.0, 32.0);   // from the top-left of the image
uniform float ppm = 24.0;                    // screen pixels per metre at the camera
uniform float bias = 0.6;
uniform vec3 light_tint = vec3(1.0);
uniform float fade = 1.0;

void vertex() {
	vec4 pv = VIEW_MATRIX * vec4(MODEL_MATRIX[3].xyz, 1.0);
	pv.xy = round(pv.xy * ppm) / ppm;
	vec2 px = vec2(UV.x * size_px.x - pivot_px.x, pivot_px.y - UV.y * size_px.y);
	pv.xy += px / ppm;
	pv.z += bias;
	POSITION = PROJECTION_MATRIX * pv;
}

void fragment() {
	vec4 c = texture(tex, UV);
	if (c.a < 0.5) discard;
	float emit = step(0.995, c.r) * step(0.55, c.g) * step(c.b, 0.62);
	ALBEDO = c.rgb * mix(light_tint, vec3(1.0), emit) * fade;
}
