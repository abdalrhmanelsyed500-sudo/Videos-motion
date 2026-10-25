// Phase 1 FULL-MISSION evidence in the REAL renderer (software WebGL2, 640x360).
// F10/F11 are harness-only PLACEMENT hooks (see render.mjs PATCHES); every mission transition
// (offer, accept, board, deliver, result, next) is real gameplay keys + real logic.
export default async (s) => {
  await s.wait(20);
  await s.shot('t00_menu.png');
  await s.key('Enter');
  await s.wait(8);
  await s.shot('t01_start.png');
  await s.hold('KeyW', 4);                    // real driving: roll east on the south ring
  await s.shot('t02_driving.png');
  await s.key('F10'); await s.wait(3);        // place at pickup ring -> offer appears
  await s.key('F9'); await s.wait(1);
  await s.shot('t03_offer.png');
  await s.key('KeyE'); await s.wait(3);       // accept -> passenger boards -> timer starts
  await s.shot('t04_boarded.png');
  await s.key('F11'); await s.wait(3);        // place inside dest ring -> delivery completes
  await s.key('F9'); await s.wait(1);
  await s.shot('t05_result.png');
  await s.key('KeyE'); await s.wait(3);       // dismiss -> next passenger spawns
  await s.shot('t06_next.png');
};
