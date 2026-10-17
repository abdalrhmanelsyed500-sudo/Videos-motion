extends Node
## Tiny leveled logger (autoload "Log"). Level can be changed at runtime from the future debug console (A7).
enum Level { DEBUG, INFO, WARN, ERROR }

var level: Level = Level.INFO


func debug(msg: String) -> void:
	_emit(Level.DEBUG, msg)


func info(msg: String) -> void:
	_emit(Level.INFO, msg)


func warn(msg: String) -> void:
	_emit(Level.WARN, msg)


func error(msg: String) -> void:
	_emit(Level.ERROR, msg)


func _emit(l: Level, msg: String) -> void:
	if l < level:
		return
	var tag := ["DBG", "INF", "WRN", "ERR"][l] as String
	if l == Level.ERROR:
		push_error(msg)
	elif l == Level.WARN:
		push_warning(msg)
	print("[%s] %s" % [tag, msg])
