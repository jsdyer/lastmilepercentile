export function bracket(speed, values, percentiles) {
  if (!Number.isFinite(speed) || speed < 0) return null;
  const equal = values.map((value, i) => value === speed ? i : -1).filter(i => i >= 0);
  if (equal.length) {
    const first = percentiles[equal[0]];
    const last = percentiles[equal.at(-1)];
    return {label: first === last ? `At P${first}` : `At the shared P${first}–P${last} cutoff`, indices: equal};
  }
  const higher = values.findIndex(value => value > speed);
  if (higher === -1) return {label: `Above P${percentiles.at(-1)}`, indices: [values.length - 1]};
  if (higher === 0) return {label: `Below P${percentiles[0]}`, indices: [0]};
  return {label: `Between P${percentiles[higher - 1]} and P${percentiles[higher]}`, indices: [higher - 1, higher]};
}
