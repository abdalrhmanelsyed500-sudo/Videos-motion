// VP-1A quick look: sailing, leave the helm, barrels, winch, nest (same hooks as deck_walk.mjs)
export default async (s) => {
  await s.wait(18);
  await s.shot('d00_helm_direct.png');
  await s.key('KeyE'); await s.wait(9); await s.shot('d02_deck_leave_helm.png');
  await s.key('KeyV'); await s.wait(2);
  await s.key('KeyK'); await s.wait(6); await s.shot('d03_barrels.png');
  await s.key('Escape'); await s.wait(1);
  await s.key('KeyJ'); await s.wait(6); await s.shot('d05_winch.png');
};
