extends RefCounted
## Benchmark for the H2D-0 prototype: runs fixed phases (path x quality x weather), measures real frame times with vsync
## off, records draw calls and memory, saves a screenshot per phase, and writes user://h2d0_bench.txt. Nothing in a
## report counts unless it came from a real run on the user's PC.
## The controller (h2d0.gd) is `ctx`: it must offer bench_apply(phase: Dictionary) and bench_capture() -> Image.
const WARM_S := 1.5
const MEASURE_S := 5.0
const TARGET_FPS := 30.0
const TARGET_LOW_FPS := 20.0
const REPORT_PATH := "user://h2d0_bench.txt"

var phases: Array = []
var results: Array = []
var active := false
var _i := -1
var _state := "idle"
var _t := 0.0
var _ms := PackedFloat64Array()


static func default_phases() -> Array:
	var out: Array = []
	for cp in [2, 1, 4, 6, 7]:
		out.append({"path": "3d", "quality": "dev_lite", "cp": cp})
	for cp in [2, 1, 6]:
		out.append({"path": "3d", "quality": "standard", "cp": cp})
	out.append({"path": "3d", "quality": "ultra", "cp": 2})
	for cp in [2, 6]:
		out.append({"path": "2d", "quality": "-", "cp": cp})
	return out


static func label(p: Dictionary) -> String:
	return "%s %s cp%d" % [str(p["path"]).to_upper(), str(p["quality"]), int(p["cp"])]


func start(ctx: Object) -> void:
	phases = default_phases()
	results.clear()
	active = true
	_i = -1
	_advance(ctx)


func step(delta: float, ctx: Object) -> void:
	if not active:
		return
	_t += delta
	if _state == "warm":
		if _t >= WARM_S:
			_state = "measure"
			_t = 0.0
			_ms.clear()
	elif _state == "measure":
		_ms.append(delta * 1000.0)
		if _t >= MEASURE_S:
			_finish(ctx)


func current_label() -> String:
	if _i < 0 or _i >= phases.size():
		return ""
	return "%d/%d %s (%s)" % [_i + 1, phases.size(), label(phases[_i]), _state]


func _advance(ctx: Object) -> void:
	_i += 1
	if _i >= phases.size():
		active = false
		_state = "done"
		return
	_state = "warm"
	_t = 0.0
	ctx.call("bench_apply", phases[_i])


func _finish(ctx: Object) -> void:
	var n := _ms.size()
	var sum := 0.0
	for x in _ms:
		sum += x
	var sorted := _ms.duplicate()
	sorted.sort()
	var p99: float = sorted[int(0.99 * float(n - 1))] if n > 0 else 0.0
	var rs := RenderingServer
	var res := {
		"label": label(phases[_i]), "path": phases[_i]["path"], "quality": phases[_i]["quality"],
		"frames": n, "avg_fps": 1000.0 * float(n) / maxf(sum, 0.001), "low1_fps": 1000.0 / maxf(p99, 0.001),
		"worst_ms": sorted[n - 1] if n > 0 else 0.0,
		"draws": int(rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)),
		"objects": int(rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)),
		"prims": int(rs.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)),
		"vram_mb": float(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)) / 1048576.0,
		"mem_mb": float(Performance.get_monitor(Performance.MEMORY_STATIC)) / 1048576.0,
	}
	var img: Image = ctx.call("bench_capture")
	if img != null:
		img.save_png("user://h2d0_bench_%02d.png" % (_i + 1))
		res.merge(frame_stats(img))
	results.append(res)
	_advance(ctx)


## Crude "is the picture sane" check on a screenshot: not flat, not black or white, not magenta (a shader error).
static func frame_stats(img: Image) -> Dictionary:
	var sum := 0.0
	var sum2 := 0.0
	var magenta := 0
	var n := 0
	for gy in 24:
		for gx in 40:
			var c := img.get_pixel((gx * img.get_width()) / 40 + 3, (gy * img.get_height()) / 24 + 3)
			var lum := 0.299 * c.r + 0.587 * c.g + 0.114 * c.b
			sum += lum
			sum2 += lum * lum
			n += 1
			if c.r > 0.9 and c.b > 0.9 and c.g < 0.2:
				magenta += 1
	var mean := sum / float(n)
	var sd := sqrt(maxf(sum2 / float(n) - mean * mean, 0.0))
	var mag := float(magenta) / float(n)
	return {"luma_mean": mean, "luma_sd": sd, "magenta": mag,
			"sane": sd > 0.02 and mean > 0.04 and mean < 0.95 and mag < 0.1}


func report(info: Dictionary) -> Array[String]:
	var out: Array[String] = ["H2D-0 BENCHMARK (real run; vsync off during the run)"]
	for k in info.keys():
		out.append("%-22s %s" % [str(k), str(info[k])])
	out.append("")
	out.append("phase (path quality weather)   | avg fps | 1% low | worst ms | draws | objects | tris | vram MB | picture")
	var lite_min_avg := 1.0e9
	var lite_min_low := 1.0e9
	var insane := 0
	for r in results:
		var pic := "n/a"
		if r.has("sane"):
			pic = "ok"
			if not r["sane"]:
				pic = "SUSPECT (mean %.2f sd %.3f magenta %.2f)" % [r["luma_mean"], r["luma_sd"], r["magenta"]]
			if not r["sane"]:
				insane += 1
		out.append("%-26s | %6.1f | %6.1f | %6.0f | %4d | %4d | %7d | %6.0f | %s" % [
				r["label"], r["avg_fps"], r["low1_fps"], r["worst_ms"], r["draws"], r["objects"], r["prims"],
				r["vram_mb"], pic])
		if r["path"] == "3d" and r["quality"] == "dev_lite":
			lite_min_avg = minf(lite_min_avg, float(r["avg_fps"]))
			lite_min_low = minf(lite_min_low, float(r["low1_fps"]))
	out.append("")
	if lite_min_avg < 1.0e8:
		var ok := lite_min_avg >= TARGET_FPS and lite_min_low >= TARGET_LOW_FPS
		var word := "MEETS TARGET" if ok else "BELOW TARGET"
		out.append("VERDICT 3D Dev-Lite: %s (worst phase avg %.1f fps, worst 1%% low %.1f fps; targets %d / %d)" % [
				word, lite_min_avg, lite_min_low, int(TARGET_FPS), int(TARGET_LOW_FPS)])
	var sanity := "all phases look sane"
	if insane > 0:
		sanity = "%d phase(s) SUSPECT: look at the screenshots" % insane
	out.append("VERDICT picture sanity: " + sanity)
	out.append("Standard and Ultra rows are information only on a machine that is not their target.")
	return out
