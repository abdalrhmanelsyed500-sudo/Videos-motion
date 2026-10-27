extends CanvasLayer
class_name AGHUD
## Retro dashboard and race overlays drawn from live gameplay state.

class DashboardPainter extends Control:
    var font: Font
    var carbon: Texture2D
    var speed := 0.0
    var rpm := 0.18
    var gear := 1
    var boost := 1.0
    var position_value := 1
    var total_racers := 6
    var race_time := 0.0
    var progress := 0.0
    var throttle := 0.0
    var brake := 0.0
    var police_level := 0
    var cockpit := true
    var countdown_text := ""
    var warning := ""
    var warning_timer := 0.0
    var crash_timer := 0.0
    var defeat_timer := 0.0
    var show_fps := false

    func _ready() -> void:
        font = ThemeDB.fallback_font
        carbon = load("res://assets/textures/carbon.png")
        set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
        mouse_filter = Control.MOUSE_FILTER_IGNORE
        texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST

    func _draw() -> void:
        var w := size.x
        var h := size.y
        _draw_top_overlays(w, h)
        if cockpit:
            _draw_cockpit(w, h)
        else:
            _draw_chase_hud(w, h)
        if countdown_text != "":
            _draw_countdown(w, h)
        if crash_timer > 0.0:
            draw_rect(Rect2(0, 0, w, h), Color(0.65, 0.08, 0.05, 0.18 * crash_timer))
            _draw_centered_text(Vector2(w * 0.5, h * 0.36), "WIPEOUT!", 64, AGPalette.c("white"), AGPalette.c("needle"))
        if defeat_timer > 0.0:
            draw_rect(Rect2(0, 0, w, h), Color(0.93, 0.91, 0.84, 0.72 * defeat_timer))
        if show_fps:
            _draw_centered_text(Vector2(w - 70, 28), "%d FPS" % int(Engine.get_frames_per_second()), 16, AGPalette.c("white"))

    func _draw_top_overlays(w: float, h: float) -> void:
        var panel_color := Color(0.045, 0.045, 0.055, 0.72)
        draw_rect(Rect2(16, 14, 250, 82), panel_color, true)
        draw_rect(Rect2(16, 14, 250, 82), AGPalette.c("amber"), false, 2.0)
        _draw_text(Vector2(28, 38), "POS  %d/%d" % [position_value, total_racers], 20, AGPalette.c("white"))
        _draw_text(Vector2(28, 65), "TIME %s" % format_time(race_time), 18, AGPalette.c("gauge"))
        draw_rect(Rect2(28, 84, 220, 5), Color(0.15, 0.14, 0.16), true)
        draw_rect(Rect2(28, 84, 220 * clampf(progress, 0.0, 1.0), 5), AGPalette.c("amber"), true)
        if police_level > 0 or warning_timer > 0.0:
            var warning_text := warning if warning_timer > 0.0 else "POLICE PURSUIT  LEVEL %d" % police_level
            draw_rect(Rect2(w - 410, 14, 394, 58), Color(0.12, 0.04, 0.04, 0.78), true)
            draw_rect(Rect2(w - 410, 14, 394, 58), AGPalette.c("needle"), false, 2.0)
            _draw_text(Vector2(w - 397, 44), warning_text, 17, AGPalette.c("white"))

    func _draw_cockpit(w: float, h: float) -> void:
        var top := h * 0.755
        var cowl := PackedVector2Array([
            Vector2(0, h), Vector2(0, top + h * 0.055),
            Vector2(w * 0.10, top + h * 0.020), Vector2(w * 0.25, top),
            Vector2(w * 0.42, top - h * 0.012), Vector2(w * 0.58, top - h * 0.012),
            Vector2(w * 0.75, top), Vector2(w * 0.90, top + h * 0.020),
            Vector2(w, top + h * 0.055), Vector2(w, h),
        ])
        draw_colored_polygon(cowl, Color(0.105, 0.095, 0.10, 1.0))
        if carbon != null:
            draw_texture_rect(carbon, Rect2(0, top, w, h - top), true, Color(0.23, 0.22, 0.22, 0.35))
        for i in range(cowl.size() - 1):
            draw_line(cowl[i], cowl[i + 1], Color(0.36, 0.33, 0.31), 2.0)
        var radius := h * 0.092
        var left := Vector2(w * 0.365, h * 0.905)
        var right := Vector2(w * 0.635, h * 0.905)
        _draw_gauge(left, radius, clampf(speed / 320.0, 0.0, 1.0), "KM/H", "%d" % int(speed))
        _draw_gauge(right, radius, clampf(rpm, 0.0, 1.0), "RPM x1000", "%.1f" % (rpm * 9.0))
        # Central gear and engine status strip.
        var gear_rect := Rect2(w * 0.475, h * 0.842, w * 0.05, h * 0.095)
        draw_rect(gear_rect, Color(0.06, 0.055, 0.06), true)
        draw_rect(gear_rect, AGPalette.c("concrete"), false, 2.0)
        _draw_centered_text(Vector2(w * 0.50, h * 0.900), str(gear), 42, AGPalette.c("white"))
        _draw_centered_text(Vector2(w * 0.50, h * 0.795), "GEAR", 14, AGPalette.c("amber"))
        var strip := Rect2(w * 0.42, h * 0.955, w * 0.16, 10)
        draw_rect(strip, Color(0.08, 0.08, 0.08), true)
        draw_rect(Rect2(strip.position.x, strip.position.y, strip.size.x * 0.55, strip.size.y), Color(0.25, 0.67, 0.25), true)
        draw_rect(Rect2(strip.position.x + strip.size.x * 0.55, strip.position.y, strip.size.x * 0.25, strip.size.y), Color(0.86, 0.70, 0.17), true)
        draw_rect(Rect2(strip.position.x + strip.size.x * 0.80, strip.position.y, strip.size.x * 0.20, strip.size.y), Color(0.78, 0.20, 0.16), true)
        var needle_x := strip.position.x + strip.size.x * clampf(rpm, 0.0, 1.0)
        draw_line(Vector2(needle_x, strip.position.y - 3), Vector2(needle_x, strip.position.y + strip.size.y + 3), AGPalette.c("white"), 2.0)
        # Acceleration / brake / boost / hazard indicators.
        _draw_indicator(Rect2(w * 0.18, h * 0.825, 74, 22), "ACCEL", throttle > 0.05, Color(0.28, 0.72, 0.32))
        _draw_indicator(Rect2(w * 0.18, h * 0.865, 74, 22), "BRAKE", brake > 0.05, Color(0.84, 0.20, 0.16))
        _draw_indicator(Rect2(w * 0.745, h * 0.825, 74, 22), "BOOST", boost > 0.02, Color(0.28, 0.62, 0.88))
        _draw_indicator(Rect2(w * 0.745, h * 0.865, 74, 22), "HAZARD", police_level > 0, Color(0.90, 0.66, 0.15))
        draw_rect(Rect2(w * 0.27, h * 0.965, w * 0.46, 8), Color(0.10, 0.10, 0.12), true)
        draw_rect(Rect2(w * 0.27, h * 0.965, w * 0.46 * clampf(boost, 0.0, 1.0), 8), Color(0.25, 0.70, 0.92), true)

    func _draw_chase_hud(w: float, h: float) -> void:
        var rect := Rect2(w - 250, h - 118, 234, 102)
        draw_rect(rect, Color(0.05, 0.05, 0.06, 0.80), true)
        draw_rect(rect, AGPalette.c("amber"), false, 2.0)
        _draw_text(Vector2(rect.position.x + 16, rect.position.y + 30), "%d KM/H" % int(speed), 28, AGPalette.c("white"))
        _draw_text(Vector2(rect.position.x + 16, rect.position.y + 62), "GEAR %d   RPM %.1f" % [gear, rpm * 9.0], 18, AGPalette.c("gauge"))
        draw_rect(Rect2(rect.position.x + 16, rect.position.y + 78, 200, 8), Color(0.12, 0.12, 0.14), true)
        draw_rect(Rect2(rect.position.x + 16, rect.position.y + 78, 200 * clampf(rpm, 0.0, 1.0), 8), AGPalette.c("needle"), true)

    func _draw_gauge(center: Vector2, radius: float, value: float, label_text: String, value_text: String) -> void:
        draw_circle(center, radius + 9, Color(0.055, 0.052, 0.055))
        draw_circle(center, radius, AGPalette.c("gauge"))
        var start_angle := deg_to_rad(135.0)
        var end_angle := deg_to_rad(405.0)
        draw_arc(center, radius * 0.84, start_angle, end_angle, 40, Color(0.16, 0.15, 0.15), 3.0, true)
        for i in range(9):
            var a: float = start_angle + (end_angle - start_angle) * float(i) / 8.0
            var inner: Vector2 = center + Vector2(cos(a), sin(a)) * radius * 0.70
            var outer: Vector2 = center + Vector2(cos(a), sin(a)) * radius * 0.82
            draw_line(inner, outer, Color(0.12, 0.11, 0.12), 2.0)
            var number_position: Vector2 = center + Vector2(cos(a), sin(a)) * radius * 0.57
            _draw_centered_text(number_position, str(i), 12, Color(0.16, 0.15, 0.15))
        var needle_angle: float = start_angle + (end_angle - start_angle) * clampf(value, 0.0, 1.0)
        var needle_end: Vector2 = center + Vector2(cos(needle_angle), sin(needle_angle)) * radius * 0.76
        draw_line(center, needle_end, AGPalette.c("needle"), 4.0, true)
        draw_circle(center, 7.0, Color(0.13, 0.12, 0.12))
        _draw_centered_text(center + Vector2(0, radius * 0.34), value_text, 21, Color(0.10, 0.10, 0.11))
        _draw_centered_text(center + Vector2(0, radius * 0.62), label_text, 13, Color(0.25, 0.24, 0.22))

    func _draw_indicator(rect: Rect2, text_value: String, active: bool, color: Color) -> void:
        draw_rect(rect, Color(0.06, 0.06, 0.07), true)
        draw_rect(rect, Color(0.35, 0.34, 0.34), false, 1.0)
        if active:
            draw_rect(rect.grow(-3), color, true)
        _draw_centered_text(Vector2(rect.position.x + rect.size.x * 0.5, rect.position.y + rect.size.y * 0.5 + 5), text_value, 12,
            Color(0.05, 0.05, 0.06) if active else Color(0.55, 0.54, 0.52))

    func _draw_countdown(w: float, h: float) -> void:
        _draw_centered_text(Vector2(w * 0.5, h * 0.36), countdown_text, 96, AGPalette.c("amber"), Color(0.05, 0.04, 0.05))

    func _draw_text(position_value_text: Vector2, text_value: String, font_size: int, color: Color) -> void:
        if font != null:
            draw_string(font, position_value_text, text_value, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)

    func _draw_centered_text(center: Vector2, text_value: String, font_size: int, color: Color, outline := Color(0, 0, 0, 0)) -> void:
        if font == null:
            return
        var width := 300.0
        var pos := Vector2(center.x - width * 0.5, center.y)
        if outline.a > 0.0:
            for dx in [-2, 2]:
                for dy in [-2, 2]:
                    draw_string(font, pos + Vector2(dx, dy), text_value, HORIZONTAL_ALIGNMENT_CENTER, width, font_size, outline)
        draw_string(font, pos, text_value, HORIZONTAL_ALIGNMENT_CENTER, width, font_size, color)

    static func format_time(seconds: float) -> String:
        var minutes := int(seconds / 60.0)
        var remainder := fmod(seconds, 60.0)
        return "%02d:%04.1f" % [minutes, remainder]

var painter: DashboardPainter
var player: AGMotorcycleController
var race_manager: AGRaceManager
var police_system: AGPoliceSystem
var camera: Node
var benchmark_mode := false

func _ready() -> void:
    layer = 5
    painter = DashboardPainter.new()
    painter.name = "DashboardPainter"
    add_child(painter)
    painter.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    painter.queue_redraw()
    painter.show_fps = bool(AGState.get_setting("show_fps", false))

func setup(player_ref: AGMotorcycleController, manager: AGRaceManager,
        police: AGPoliceSystem, camera_ref: Node) -> void:
    player = player_ref
    race_manager = manager
    police_system = police
    camera = camera_ref

func _process(delta: float) -> void:
    if painter == null:
        return
    painter.warning_timer = maxf(0.0, painter.warning_timer - delta)
    painter.crash_timer = maxf(0.0, painter.crash_timer - delta)
    painter.defeat_timer = maxf(0.0, painter.defeat_timer - delta)
    if not benchmark_mode and player != null and is_instance_valid(player):
        painter.speed = player.speed * 3.6
        painter.rpm = player.rpm
        painter.gear = player.gear
        painter.boost = player.boost_energy
        painter.throttle = float(player.last_input.get("throttle", 0.0))
        painter.brake = float(player.last_input.get("brake", 0.0)) + float(player.last_input.get("handbrake", 0.0))
        if race_manager != null:
            var state: Dictionary = race_manager.get_state()
            painter.position_value = int(state.get("position", 1))
            painter.total_racers = int(state.get("total", 6))
            painter.race_time = float(state.get("time", 0.0))
            painter.progress = float(state.get("progress", 0.0))
        if police_system != null:
            painter.police_level = int(police_system.get_state().get("level", 0))
    painter.queue_redraw()

func set_cockpit_mode(value: bool) -> void:
    if painter != null:
        painter.cockpit = value
        painter.queue_redraw()

func set_countdown(text_value: String) -> void:
    if painter != null:
        painter.countdown_text = text_value
        painter.queue_redraw()

func set_police_alert(level: int, message: String) -> void:
    if painter != null:
        painter.police_level = level
        painter.warning = message
        painter.warning_timer = 4.0
        painter.queue_redraw()

func show_warning(message: String) -> void:
    if painter != null:
        painter.warning = message
        painter.warning_timer = 2.5
        painter.queue_redraw()

func show_crash_overlay(reason: String) -> void:
    if painter != null:
        painter.warning = reason
        painter.warning_timer = 4.0
        painter.crash_timer = 1.4
        painter.queue_redraw()

func show_defeat_transition() -> void:
    if painter != null:
        painter.defeat_timer = 0.9
        painter.queue_redraw()

func set_benchmark_state(speed_kmh: float, rpm_value: float, gear_value: int,
        position_value: int, elapsed: float, progress_value: float,
        boost_value: float, police_level: int) -> void:
    benchmark_mode = true
    if painter == null:
        return
    painter.speed = speed_kmh
    painter.rpm = rpm_value
    painter.gear = gear_value
    painter.position_value = position_value
    painter.race_time = elapsed
    painter.progress = progress_value
    painter.boost = boost_value
    painter.police_level = police_level
    painter.countdown_text = ""
    painter.cockpit = true
    painter.queue_redraw()
