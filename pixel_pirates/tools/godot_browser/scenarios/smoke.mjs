export default async (s) => {
  for (let i = 1; i <= 6; i++) { await s.wait(10); await s.shot(`smoke_${i}.png`); }
};
