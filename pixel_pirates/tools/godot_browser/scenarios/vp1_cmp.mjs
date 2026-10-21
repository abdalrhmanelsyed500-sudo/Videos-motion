// VP-1A before/after: HUD debug text off (F3), then: at sea, leave the helm, barrels, winch, cabin, ladder, nest.
export default async (s) => {
  await s.wait(14);
  await s.key('F3'); await s.wait(3);
  await s.shot('s00_sea.png');
  await s.key('KeyE'); await s.wait(9); await s.shot('s01_deck.png');
  await s.key('KeyV'); await s.wait(2);
  await s.key('KeyK'); await s.wait(6); await s.shot('s02_barrels.png');
  await s.key('Escape'); await s.wait(1);
  await s.key('KeyJ'); await s.wait(6); await s.shot('s03_winch.png');
  await s.key('KeyO'); await s.wait(6); await s.shot('s04_cabin.png');
  await s.key('KeyI'); await s.wait(10); await s.shot('s05_nest.png');
};
