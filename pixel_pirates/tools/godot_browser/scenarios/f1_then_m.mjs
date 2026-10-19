// The deterministic P1 repro candidate: F1 (documented as "quality" in the r3-r5 notes) opens the debug console, which grabs focus
// and then swallows M. Needs RENDER_REGEX_SHIM=1 so that the console autoload compiles in the web template.
export default async (s) => {
  await s.wait(20);
  await s.key('F1'); await s.wait(4); await s.shot('f1_console.png');
  await s.key('KeyM'); await s.wait(5); await s.shot('f1_then_M.png');
};
