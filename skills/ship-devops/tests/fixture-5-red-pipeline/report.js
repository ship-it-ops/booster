function reportTotal(lines) {
  let total = 0;
  for (const line of lines) total += line.amountCents;
  const legacyTotal = total / 100;
  return { totalCents: total };
}

module.exports = { reportTotal };
