// CP-2 Release B in a real renderer at 1366x876: the winch prompt on deck, F into the first-person view, the needle, the haul HUD, a surge
// warning, the net coming up with the real catch, the catch card, the unload and the storage panel. Hook Z (render.mjs) nudges the stage
// machine so the software renderer does not have to run real time; keys F, E, Escape are real.
export default async (s) => {
  await s.wait(20);
  await s.key('KeyE'); await s.wait(5);                      // leave the helm
  await s.key('KeyZ'); await s.wait(4);                      // 1: ship on the Blue Drop, pirate at the winch
  await s.shot('f00_winch_prompt.png');
  await s.key('KeyF'); await s.wait(3); await s.shot('f01_enter.png');
  await s.wait(4); await s.key('KeyZ'); await s.wait(2); await s.shot('f02_aim.png');
  await s.key('KeyZ'); await s.wait(3); await s.shot('f03_haul.png');
  await s.key('KeyZ'); await s.wait(2); await s.shot('f04_surge.png');
  await s.key('KeyZ'); await s.wait(0.4); await s.shot('f05_raise.png');
  await s.key('KeyZ'); await s.wait(2); await s.shot('f06_card.png');
  await s.key('KeyZ'); await s.wait(0.6); await s.shot('f07_unload.png');
  await s.wait(8); await s.shot('f08_back_on_deck.png');
  await s.key('KeyF'); await s.wait(3);
  await s.key('KeyZ'); await s.wait(2); await s.shot('f09_fail.png');   // 8: a lost haul (the hook counter continues)
  await s.key('KeyE'); await s.wait(3);
  await s.key('KeyZ'); await s.wait(3);                                 // 9: barrels with three species
  await s.key('KeyE'); await s.wait(3); await s.shot('f10_storage_panel.png');
};
