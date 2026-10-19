export default async (s) => {
  await s.wait(20);
  await s.rawKey('KeyM', 'ة', 77);          // Arabic layout, physical M
  await s.wait(6); await s.shot('ar1_open.png');
  await s.rawKey('Escape', 'Escape', 27); await s.wait(5); await s.shot('ar2_closed.png');
  await s.key('KeyM'); await s.wait(5); await s.shot('ar3_open_again.png');
};
