// VP-1A ocean: open water far from the cay, day / sunset / dusk / night (N cycles the time of day), then the low-cost profile (F1).
export default async (s) => {
  await s.wait(10);
  await s.key('F3'); await s.wait(2);
  await s.key('Digit2'); await s.wait(10); await s.shot('o0_open_day.png');
  await s.key('KeyN'); await s.wait(8); await s.shot('o1_time2.png');
  await s.key('KeyN'); await s.wait(8); await s.shot('o2_time3.png');
  await s.key('KeyN'); await s.wait(8); await s.shot('o3_time4.png');
  await s.key('KeyN'); await s.wait(8); await s.shot('o4_time5.png');
};
