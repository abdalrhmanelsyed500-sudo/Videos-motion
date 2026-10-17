extends Node
## Global event bus (autoload "Bus"). Systems talk through signals so no system imports another (A1-7: achievements are
## just events here; a store adapter can listen later). Add a signal here ONLY when two or more systems need it.

@warning_ignore("unused_signal")
signal achievement_unlocked(id: String)
@warning_ignore("unused_signal")
signal quality_changed(profile_name: String)
@warning_ignore("unused_signal")
signal asset_missing(asset_id: String)
