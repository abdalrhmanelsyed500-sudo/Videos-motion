// r6: the whole loop through the real renderer and real key events: ashore, talk to Pip (poor), +25 reales (F6), hire, the fish
// counter and the sell panel, F8 self-check, then the map. Screenshots go to SHOT_DIR; run it at several VIEW_W x VIEW_H.
export default async (s) => {
  await s.wait(18);
  await s.key('F9'); await s.wait(6);
  await s.key('F10'); await s.wait(4); await s.shot('fl0_near_pip.png');
  await s.key('KeyE'); await s.wait(4); await s.shot('fl1_pip_intro.png');
  await s.key('Enter'); await s.wait(2); await s.key('Enter'); await s.wait(2); await s.key('Enter'); await s.wait(3); await s.shot('fl2_pip_hub_poor.png');
  await s.key('Escape'); await s.wait(3);
  await s.key('F6'); await s.wait(2); await s.key('F6'); await s.wait(2);
  await s.key('KeyE'); await s.wait(4); await s.shot('fl3_pip_hub_afford.png');
  await s.key('Escape'); await s.wait(3);
  await s.key('F7'); await s.wait(2);
  await s.key('F11'); await s.wait(4); await s.shot('fl4_near_counter.png');
  await s.key('KeyE'); await s.wait(5); await s.shot('fl5_fishmonger.png');
  await s.key('Escape'); await s.wait(3);
  await s.key('KeyM'); await s.wait(5); await s.shot('fl6_map.png');
  await s.key('Escape'); await s.wait(3);
  await s.key('F8'); await s.wait(10); await s.shot('fl7_f8.png');
};
