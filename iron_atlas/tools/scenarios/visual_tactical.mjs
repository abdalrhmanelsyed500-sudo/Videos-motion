// Render the actual tactical scene using the explicitly documented contact fixture.
export default async (s) => {
  await s.wait(6);
  await s.shot('07_tactical_fixture.png');
};
