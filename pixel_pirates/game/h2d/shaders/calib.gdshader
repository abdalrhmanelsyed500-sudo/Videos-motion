// Gamma calibration probe: outputs mid-grey through h2d_out(). sea_view_3d.gd reads the pixel back once at start-up and
// sets h2d_gamma to whichever of 2.2 / 1.0 makes the screen show 0.5. (Compatibility may or may not encode sRGB itself.)
shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled, depth_test_disabled;

#include "res://h2d/shaders/h2d_common.gdshaderinc"

void fragment() {
	ALBEDO = pow(vec3(0.5), vec3(h2d_gamma));
}
