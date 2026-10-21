// VP-1A.2 lighting comparison, same camera for every build: on foot at mid-deck (hook \ places the pirate), at five times of the day (N cycles them).
export default async (s) => {
  await s.wait(12);
  await s.key('F3'); await s.wait(2);
  await s.key('KeyE'); await s.wait(8);
  await s.key('Backslash'); await s.wait(6);
  await s.shot('L0_mid_t0.png');
  await s.key('KeyN'); await s.wait(5); await s.shot('L1_mid_t1.png');
  await s.key('KeyN'); await s.wait(5); await s.shot('L2_mid_t2.png');
  await s.key('KeyN'); await s.wait(5); await s.shot('L3_mid_t3.png');
  await s.key('KeyN'); await s.wait(5); await s.shot('L4_mid_t4.png');
};
