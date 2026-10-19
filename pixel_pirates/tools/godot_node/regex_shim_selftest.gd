extends SceneTree
const RegEx := preload("res://core/regex_shim.gd")
## Self-test of the harness-only RegEx polyfill against the patterns the project uses (expected results written by hand).
var fails := 0
var n := 0


func t(pat: String, subj: String, want: bool) -> void:
	n += 1
	var re = RegEx.create_from_string(pat)
	var got: bool = re.is_valid() and re.search(subj) != null
	if got != want:
		fails += 1
		print("  FAIL: /%s/ on '%s' wanted %s" % [pat, subj, str(want)])


func _initialize() -> void:
	t("^[a-z]+(_[a-z0-9]+)+$", "spc_mackerel", true)
	t("^[a-z]+(_[a-z0-9]+)+$", "spc_", false)
	t("^[a-z]+(_[a-z0-9]+)+$", "Spc_a", false)
	t("^[a-z]+(_[a-z0-9]+)+$", "isl_901_x2", true)
	t("^[a-z]+(_[a-z0-9]+)+$", "nounderscore", false)
	t("^isl_[0-9]{3}$", "isl_901", true)
	t("^isl_[0-9]{3}$", "isl_91", false)
	t("^isl_[0-9]{3}$", "isl_9011", false)
	t("^[a-z_]{1,24}$", "reg_kettle_seas", true)
	t("^[a-z_]{1,24}$", "Reg", false)
	t("^[a-z_]{1,24}$", "", false)
	t("^[0-9]{1,20}$", "18446744073709551615", true)
	t("^[0-9]{1,20}$", "abc", false)
	t("^[0-9]{1,20}$", "123456789012345678901", false)
	t("^[A-Za-z0-9_-]{1,32}$", "a7_console_test", true)
	t("^[A-Za-z0-9_-]{1,32}$", "../evil", false)
	t("^[A-Za-z0-9_-]{1,32}$", "a-b_C9", true)
	t("^.{2,40}$", "ab", true)
	t("^.{2,40}$", "a", false)
	t("^[A-Z][0-9]{1,2}$", "C12", true)
	t("^[A-Z][0-9]{1,2}$", "C123", false)
	t("^[a-z][a-z0-9_]*$", "abc_9", true)
	t("^[a-z][a-z0-9_]*$", "9abc", false)
	t("^(isl_[0-9]{3})?$", "", true)
	t("^(isl_[0-9]{3})?$", "isl_001", true)
	t("^(isl_[0-9]{3})?$", "isl_01", false)
	t("a|b", "xxb", true)
	t("^(", "x", false)
	print("REGEX SHIM: %d checks, %d failed -> %s" % [n, fails, "PASS" if fails == 0 else "FAIL"])
	quit(0 if fails == 0 else 1)
