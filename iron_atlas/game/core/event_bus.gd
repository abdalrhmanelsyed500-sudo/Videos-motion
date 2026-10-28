extends Node
## EventBus: decoupled signals for important state changes (architecture rule:
## systems emit, UI/other systems listen; no node-path coupling).

signal day_passed(day: int)
signal week_passed(week: int)
signal month_passed(month: int)
signal region_controller_changed(region_id: String, new_controller: String)
signal formation_created(formation_id: String)
signal formation_defeated(formation_id: String)
signal order_status_changed(order_id: String, status: String)
signal battle_finished(report: Dictionary)
signal war_started(war_id: String)
signal war_ended(war_id: String)
signal relations_changed(pair_key: String)
signal notification(text: String, priority: int)
signal campaign_ended(outcome: String)
