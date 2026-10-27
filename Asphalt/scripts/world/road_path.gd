extends RefCounted
class_name AGRoadPath
## Single source of truth for road geometry, lanes, elevation and race progress.

const START_Z := 200.0
const FINISH_Z := -4600.0
const RACE_LENGTH := 4800.0
const SEGMENT_LENGTH := 24.0
const LANE_WIDTH := 3.6
const LANE_COUNT := 4
const ROAD_WIDTH := 16.8
const ROAD_HALF_WIDTH := 8.4
const SHOULDER_WIDTH := 2.4
const BARRIER_OFFSET := 9.7

static func center_x(z: float) -> float:
    return 11.0 * sin(z * 0.00135) + 7.0 * sin(z * 0.00047)

static func tangent_x(z: float) -> float:
    return 11.0 * 0.00135 * cos(z * 0.00135) + 7.0 * 0.00047 * cos(z * 0.00047)

static func height_at(z: float) -> float:
    return 0.65 * sin(z * 0.0012) + 0.35 * sin(z * 0.0026)

static func lane_offset(lane: int) -> float:
    return -5.4 + float(clampi(lane, 0, LANE_COUNT - 1)) * LANE_WIDTH

static func lane_x(z: float, lane: int) -> float:
    return center_x(z) + lane_offset(lane)

static func lane_from_x(z: float, x: float) -> int:
    return clampi(int(round((x - center_x(z) + 5.4) / LANE_WIDTH)), 0, LANE_COUNT - 1)

static func clamp_x(z: float, x: float, margin := 0.75) -> float:
    return clampf(x, center_x(z) - ROAD_HALF_WIDTH + margin, center_x(z) + ROAD_HALF_WIDTH - margin)

static func yaw_at(z: float) -> float:
    return atan(tangent_x(z))

static func progress(z: float) -> float:
    return clampf((START_Z - z) / RACE_LENGTH, 0.0, 1.0)

static func is_bridge(z: float) -> bool:
    return z < -2300.0 and z > -3400.0
