export default async (s) => {
  await s.wait(18);
  await s.key('F9'); await s.wait(8); await s.shot('as0_ashore.png');
  await s.key('KeyM'); await s.wait(6); await s.shot('as1_M_ashore.png');
  await s.key('Digit2'); await s.wait(4); await s.shot('as2_island.png');
  await s.key('Escape'); await s.wait(5); await s.shot('as3_esc.png');
  await s.rawKey('KeyM', 'ة', 77); await s.wait(6); await s.shot('as4_M_arabic.png');
};
