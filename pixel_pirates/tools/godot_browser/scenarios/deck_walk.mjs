// CP-2 Release A in a real renderer at 1366x876: the helm (direct, course hold), leaving the helm, the main deck, the cabin roof dissolve,
// barrels, winch, half way up the rope ladder, the crow's nest, the sleeping deck and the hold. Hooks Q U I O J K L H V (render.mjs) only place the pirate.
export default async (s) => {
  await s.wait(18);
  await s.shot('d00_helm_direct.png');
  await s.key('KeyC'); await s.wait(3); await s.shot('d01_helm_hold.png');
  await s.key('KeyE'); await s.wait(9); await s.shot('d02_deck_leave_helm.png');
  await s.key('KeyV'); await s.wait(2);
  await s.key('KeyK'); await s.wait(6); await s.shot('d03_barrels.png');
  await s.key('KeyE'); await s.wait(3); await s.shot('d04_fish_panel.png');
  await s.key('Escape'); await s.wait(1);
  await s.key('KeyJ'); await s.wait(6); await s.shot('d05_winch.png');
  await s.key('KeyO'); await s.wait(6); await s.shot('d06_cabin_inside.png');
  await s.key('KeyL'); await s.wait(8); await s.shot('d07_ladder_half.png');
  await s.key('KeyI'); await s.wait(10); await s.shot('d08_nest.png');
  await s.key('KeyQ'); await s.wait(8); await s.shot('d09_sleeping.png');
  await s.key('KeyU'); await s.wait(8); await s.shot('d10_hold_hatch.png');
  await s.key('KeyH'); await s.wait(6); await s.shot('d11_hold_racks.png');
  await s.key('KeyE'); await s.wait(2); await s.shot('d12_provisions.png');
};
