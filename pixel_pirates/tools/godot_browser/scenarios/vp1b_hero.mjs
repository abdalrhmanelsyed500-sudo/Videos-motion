// VP-1A.2 hero scene: the real deck at midships on the STANDARD profile, at day, sunset and night, plus one Dev-Lite night frame.
// Same key order in every build, so before/after pairs share camera, pose and light.
export default async (s) => {
  await s.wait(12);
  await s.key('F1'); await s.wait(5);
  await s.key('KeyE'); await s.wait(8);
  await s.key('Backslash'); await s.wait(4);
  await s.key('F3'); await s.wait(3);
  await s.shot('H0_day.png');
  await s.key('KeyN'); await s.wait(5);
  await s.key('KeyN'); await s.wait(5); await s.shot('H1_sunset.png');
  await s.key('KeyN'); await s.wait(5); await s.shot('H2_night.png');
  await s.key('F1'); await s.wait(3);
  await s.key('F1'); await s.wait(5); await s.shot('H3_night_lite.png');
};
