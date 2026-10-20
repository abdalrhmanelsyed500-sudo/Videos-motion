// CP-1 map replacement through the real renderer at the real window size: sea (button click opens it), three tabs, zoom, drag pan,
// Esc; then ashore (F9) with M, the Arabic layout, and the closed state again. Screenshots go to SHOT_DIR.
export default async (s) => {
  const VW = Number(process.env.VIEW_W || 1366), VH = Number(process.env.VIEW_H || 876);
  await s.wait(20);
  await s.shot('ms0_sea_closed.png');
  const m0 = s.mark();
  // the corner "MAP [M]" button (bottom right; the 1280x720 base is scaled to fit and centred)
  const k = Math.min(VW / 1280, VH / 720), ox = (VW - 1280 * k) / 2, oy = (VH - 720 * k) / 2;
  await s.page.mouse.click(ox + (1280 - 82) * k, oy + (720 - 33) * k);
  await s.wait(6); await s.shot('ms1_button_opened_sea.png');
  await s.key('Digit1'); await s.wait(4); await s.shot('ms2_city.png');
  await s.key('Digit2'); await s.wait(4); await s.shot('ms3_island.png');
  await s.key('Digit3'); await s.wait(4); await s.shot('ms4_sea.png');
  for (let i = 0; i < 3; i++) { await s.key('Equal'); await s.wait(1); }
  await s.shot('ms5_zoomed.png');
  await s.hold('ArrowRight', 1.2); await s.wait(2); await s.shot('ms6_panned_keys.png');
  await s.page.mouse.move(VW / 2, VH / 2); await s.page.mouse.down(); await s.page.mouse.move(VW / 2 - 140, VH / 2 + 90, { steps: 8 }); await s.page.mouse.up();
  await s.wait(3); await s.shot('ms7_dragged.png');
  await s.key('Home'); await s.wait(2);
  await s.key('Escape'); await s.wait(4); await s.shot('ms8_closed_esc.png');
  console.log('LOG sea:', JSON.stringify(s.logSince(m0).filter((l) => /map|Map|MAP|ERROR|rror/.test(l)).slice(-10)));
  await s.key('F9'); await s.wait(8); await s.shot('ms9_ashore.png');
  await s.key('KeyM'); await s.wait(6); await s.shot('ms10_ashore_M.png');
  await s.key('Digit2'); await s.wait(4); await s.shot('ms11_ashore_island.png');
  await s.key('KeyM'); await s.wait(4); await s.shot('ms12_closed_M.png');
  await s.rawKey('KeyM', 'ة', 77); await s.wait(6); await s.shot('ms13_arabic_M.png');
  await s.key('Escape'); await s.wait(4);
  await s.hold('KeyD', 1.0); await s.wait(2); await s.shot('ms14_walk_after_close.png');
};
