extends Node
## Loads procedural WAV placeholders and keeps engine/siren audio in sync.

const AUDIO_DIR := "res://assets/audio/"

var streams: Dictionary = {}
var engine_player: AudioStreamPlayer
var ambience_player: AudioStreamPlayer
var siren_player: AudioStreamPlayer
var one_shot_players: Array = []
var next_one_shot: int = 0
var siren_active := false

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    for file_name in [
        "engine_loop", "traffic_ambience", "siren_loop", "countdown_beep", "race_go",
        "collision_minor", "collision_major", "hospital_sting", "victory_sting",
        "menu_click", "police_alert", "boost",
    ]:
        var stream: AudioStream = load(AUDIO_DIR + file_name + ".wav")
        if stream == null:
            push_warning("Missing generated audio: " + file_name)
            continue
        _configure_loop(file_name, stream)
        streams[file_name] = stream
    engine_player = _make_player("EnginePlayer", true)
    ambience_player = _make_player("AmbiencePlayer", true)
    siren_player = _make_player("SirenPlayer", true)
    engine_player.stream = streams.get("engine_loop")
    ambience_player.stream = streams.get("traffic_ambience")
    siren_player.stream = streams.get("siren_loop")
    for i in range(8):
        one_shot_players.append(_make_player("SFX%d" % i, false))

func _make_player(node_name: String, looping: bool) -> AudioStreamPlayer:
    var player := AudioStreamPlayer.new()
    player.name = node_name
    player.bus = "Master"
    player.volume_db = -80.0
    player.autoplay = false
    add_child(player)
    return player

func _configure_loop(file_name: String, stream: AudioStream) -> void:
    if not (stream is AudioStreamWAV):
        return
    if file_name in ["engine_loop", "traffic_ambience", "siren_loop"]:
        stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
        stream.loop_begin = 0
        stream.loop_end = 0

func play(sound_name: String, volume_db := 0.0, pitch := 1.0) -> void:
    if not streams.has(sound_name) or one_shot_players.is_empty():
        return
    var player: AudioStreamPlayer = one_shot_players[next_one_shot]
    next_one_shot = (next_one_shot + 1) % one_shot_players.size()
    player.stream = streams[sound_name]
    player.volume_db = volume_db
    player.pitch_scale = maxf(0.05, pitch)
    player.play()

func start_race_audio() -> void:
    if engine_player.stream != null and not engine_player.playing:
        engine_player.play()
    if ambience_player.stream != null and not ambience_player.playing:
        ambience_player.play()
    set_engine_state(0.0, 0.18, 0.0)
    set_siren(false, 0.0)

func stop_race_audio() -> void:
    engine_player.stop()
    ambience_player.stop()
    siren_player.stop()
    siren_active = false

func set_engine_state(speed: float, rpm: float, throttle: float) -> void:
    if engine_player == null:
        return
    engine_player.pitch_scale = clampf(0.62 + rpm * 1.45 + speed * 0.004, 0.6, 2.45)
    engine_player.volume_db = -21.0 + clampf(throttle, 0.0, 1.0) * 5.0 + clampf(speed / 90.0, 0.0, 1.0) * 3.0
    ambience_player.volume_db = -22.0 + clampf(speed / 90.0, 0.0, 1.0) * 4.0

func set_siren(active: bool, intensity: float = 1.0) -> void:
    if siren_player == null:
        return
    siren_active = active
    if active:
        siren_player.volume_db = -14.0 + clampf(intensity, 0.0, 1.0) * 5.0
        siren_player.pitch_scale = 0.95 + clampf(intensity, 0.0, 1.0) * 0.16
        if not siren_player.playing:
            siren_player.play()
    else:
        siren_player.volume_db = -80.0
        siren_player.stop()

func play_ui_click() -> void:
    play("menu_click", -10.0, 1.0)
