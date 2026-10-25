// Phase 1 evidence run in the REAL renderer (software WebGL2) + F9 state dumps.
export default async (s) => {
  await s.wait(25);
  await s.shot('t00_menu.png');
  await s.key('Enter');
  await s.wait(12);
  await s.key('F9'); await s.wait(1);
  await s.shot('t01_start.png');
  await s.hold('KeyW', 8);
  await s.key('F9'); await s.wait(1);
  await s.shot('t02_driving.png');
  await s.hold('KeyA', 1.2);
  await s.hold('KeyW', 6);
  await s.key('F9'); await s.wait(1);
  await s.shot('t03_market.png');
};
