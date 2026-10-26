// Phase 2 DRIVING-QUALITY evidence in the REAL renderer (software WebGL2, 640x360).
// Harness-only PLACEMENT hooks (render.mjs PATCHES, district.gd): F6 speed-straight run east on
// the south ring, F7 diagonal alley, F8 collision course at the parked car, F10 pickup ring,
// F11 dest ring, F12 ramp approach. They only place the vehicle (pos/yaw/speed, zeroed slip).
// EVERYTHING after placement is real keys and real game logic: acceleration, drift, impact
// response, ramp launch/landing, reversing, the whole mission flow. F9 dumps real state (TKDBG)
// into page.log as ground truth per shot. NOTE: software GL time dilation (fps varies with view
// complexity, observed ~15-35x): waits are real seconds and events are bracketed with shot/dump
// bursts; this is evidence-capture timing, never a performance measurement.
export default async (s) => {
  await s.wait(15);
  await s.shot('t00_menu.png');
  await s.key('Enter');                       // real start
  await s.wait(8);
  await s.key('F9'); await s.wait(1);         // dump: spawned at start spot facing east
  await s.shot('t01_start.png');

  // --- 1) speed straight: F6 east along the south ring at 10 m/s, throttle to top end
  await s.key('F6');
  let hw = s.hold('KeyW', 30);                // un-awaited: shoot WHILE accelerating
  await s.wait(22);
  await s.key('F9');
  await s.shot('t02_speed_straight.png');     // smoothed follow + speed-linked FOV
  await hw;

  // --- 2) controlled drift: throttle + steer + handbrake, then traction recovery
  hw = s.hold('KeyW', 26);
  let ha = s.hold('KeyD', 26);
  let hb = s.hold('Space', 26);
  await s.wait(20);
  await s.key('F9');
  await s.shot('t03_drift.png');              // lateral slip + body roll, clamped
  await Promise.all([hw, ha, hb]);
  await s.wait(5);
  await s.shot('t04_drift_exit.png');         // grip restored, no stuck slide

  // --- 3) collision feedback: F8 places 8.5 m from the parked car at 12 m/s, facing it
  await s.key('F8');
  await s.wait(9);
  await s.key('F9'); await s.wait(1);         // dump: stopped at the car, no penetration
  await s.shot('t05_impact.png');             // around the contact frame (shake + HUD penalty)
  await s.wait(5);
  await s.shot('t05b_impact_settled.png');    // shake decayed, single penalty (cooldown)

  // --- 4) ramp jump: F12 west at 16 m/s -> ramp trigger at (-40, 60); burst-bracket the air
  await s.key('F12');
  // OBSERVATIONAL airborne capture: poll F9 dumps (~0.4 s cadence) and shoot the instant a
  // dump reports the tuk-tuk above the road (y > 0.5). Nothing is nudged - we only look.
  const dumpY = (lines) => {
    for (let i = lines.length - 1; i >= 0; i -= 1) {
      const m = lines[i].match(/tuk=\([-\d.]+, (-[\d.]+|[\d.]+), [-\d.]+\)/);
      if (m) return Number(m[1]);
    }
    return null;
  };
  let airShots = 0;
  for (let i = 0; i < 16 && airShots < 2; i += 1) {
    const n = s.mark();
    await s.key('F9');
    await s.wait(0.25);
    const y = dumpY(s.logSince(n));
    if (y != null && y > 0.5) {
      airShots += 1;
      await s.shot(`t06_air_${airShots}.png`);
    }
  }
  if (airShots === 0) await s.shot('t06_air_1.png');   // never above road: honest miss
  await s.wait(3);
  await s.key('F9'); await s.wait(1);         // dump: landed, y back on the road
  await s.shot('t07_landed.png');             // landing feedback, control retained

  // --- 5) narrow diagonal alley (F7) + reversing readability
  await s.key('F7');
  hw = s.hold('KeyW', 12);
  await s.wait(2.5);
  await s.key('F9');
  await s.shot('t08_alley.png');              // tight-street framing mid-alley
  await hw;
  const hr = s.hold('KeyS', 30);              // brake to stop, then reverse
  await s.wait(26);
  await s.key('F9');                          // dump: reversing
  await s.shot('t09_reverse.png');            // camera stays behind, pulled in
  await hr;

  // --- 6) full mission under stress: accept, drift for the bonus, deliver, result card
  await s.key('F10'); await s.wait(3);        // pickup ring -> offer appears
  await s.key('KeyE'); await s.wait(3);       // accept -> passenger boards, timer runs
  hw = s.hold('KeyW', 28);
  await s.wait(26);                           // build speed on mission (real driving)
  await hw;
  hw = s.hold('KeyW', 24);
  ha = s.hold('KeyD', 24);
  hb = s.hold('Space', 24);
  await s.wait(18);
  await s.shot('t10_mission_drift.png');      // drifting mid-mission
  await Promise.all([hw, ha, hb]);
  await s.wait(6);
  await s.shot('t11_drift_bonus_toast.png');  // "Controlled drift! +E£n" on slip release
  await s.key('F11'); await s.wait(3);        // dest ring -> delivery completes
  await s.key('F9'); await s.wait(1);         // dump: state=4 (result)
  await s.shot('t12_result.png');             // result card incl. the drift bonus term
};
