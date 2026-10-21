// VP-0: let a prototype scene settle, then take one shot. Scene and look come from the extra Godot args (see vp0_stage.gd).
export default async (s) => {
  await s.wait(Number(process.env.VP0_WAIT ?? 14));
  await s.shot(process.env.VP0_NAME ?? 'vp0.png');
};
