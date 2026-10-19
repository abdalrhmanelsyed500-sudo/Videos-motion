export default async (s) => {
  await s.wait(20);
  await s.shot('m0_before.png');
  const m0 = s.mark();
  await s.key('KeyM');
  await s.wait(6);
  await s.shot('m1_after_M.png');
  console.log('LOG after M:', JSON.stringify(s.logSince(m0).slice(-12)));
  await s.key('Digit2'); await s.wait(5); await s.shot('m2_island.png');
  await s.key('Digit3'); await s.wait(5); await s.shot('m3_sea.png');
  await s.key('KeyM'); await s.wait(5); await s.shot('m4_closed.png');
};
