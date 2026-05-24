const defaults = {
  voltage: 11,
  mva: 10,
  zPercent: 5.75,
  length: 4.2,
  r1: 0.306,
  x1: 0.386,
  location: 62,
  relayPickup: 800,
  faultType: "single_line_ground",
};

const faultMultipliers = {
  three_phase: 1,
  line_to_line: 0.866,
  single_line_ground: 0.65,
};

const elements = Object.fromEntries(
  Object.keys(defaults).map((id) => [id, document.getElementById(id)]),
);

const output = {
  locationKm: document.getElementById("locationKm"),
  faultGroup: document.getElementById("faultGroup"),
  faultLabel: document.getElementById("faultLabel"),
  faultCurrent: document.getElementById("faultCurrent"),
  puVoltage: document.getElementById("puVoltage"),
  faultMva: document.getElementById("faultMva"),
  xrRatio: document.getElementById("xrRatio"),
  severityBadge: document.getElementById("severityBadge"),
  primaryDevice: document.getElementById("primaryDevice"),
  tripSummary: document.getElementById("tripSummary"),
  deviceRows: document.getElementById("deviceRows"),
  baseCurrent: document.getElementById("baseCurrent"),
  totalPu: document.getElementById("totalPu"),
  backupDevice: document.getElementById("backupDevice"),
  chart: document.getElementById("curveChart"),
};

function number(id) {
  return Number(elements[id].value);
}

function inverseTime(current, pickup, dial) {
  if (current <= pickup) return 999;
  const multiple = current / pickup;
  const seconds = (dial * 0.14) / (Math.pow(multiple, 0.02) - 1);
  return Math.max(0.03, Math.min(999, seconds));
}

function devices(length, relayPickup) {
  return [
    { name: "Fuse-2", type: "Fuse", location: length * 0.78, pickup: 1500, dial: 0.055 },
    { name: "Fuse-1", type: "Fuse", location: length * 0.45, pickup: 1800, dial: 0.095 },
    { name: "CB-2 Relay", type: "Circuit Breaker", location: 0.15, pickup: relayPickup, dial: 0.8 },
    { name: "CB-1 Source", type: "Circuit Breaker", location: 0, pickup: relayPickup, dial: 1.2 },
  ];
}

function calculate() {
  const voltage = number("voltage");
  const mva = number("mva");
  const zPercent = number("zPercent");
  const length = number("length");
  const r1 = number("r1");
  const x1 = number("x1");
  const locationPercent = number("location");
  const relayPickup = number("relayPickup");
  const faultType = elements.faultType.value;

  const baseCurrent = (mva * 1_000_000) / (Math.sqrt(3) * voltage * 1000);
  const baseImpedance = Math.pow(voltage * 1000, 2) / (mva * 1_000_000);
  const locationKm = length * (locationPercent / 100);
  const feederR = locationKm * r1;
  const feederX = locationKm * x1;
  const feederZ = Math.hypot(feederR, feederX);
  const sourcePu = zPercent / 100;
  const feederPu = feederZ / baseImpedance;
  const totalPu = sourcePu + feederPu;
  const threePhaseCurrent = baseCurrent / totalPu;
  const faultCurrent = threePhaseCurrent * faultMultipliers[faultType];
  const faultMva = (Math.sqrt(3) * voltage * faultCurrent) / 1000;
  const puVoltage = Math.min(1, Math.max(0, feederPu / totalPu));
  const xrRatio = feederR === 0 ? 999 : feederX / feederR;
  const severity =
    faultCurrent >= 10000
      ? "critical"
      : faultCurrent >= 5000
        ? "high"
        : faultCurrent >= 2000
          ? "elevated"
          : "normal";

  const deviceList = devices(length, relayPickup)
    .filter((device) => device.location <= locationKm + 0.001)
    .map((device) => ({
      ...device,
      tripTime: inverseTime(faultCurrent, device.pickup, device.dial),
    }))
    .sort((a, b) => b.location - a.location);

  const ranked = deviceList.length ? deviceList : devices(length, relayPickup);
  const primary = ranked[0];
  const backup = ranked[1] || ranked[0];

  return {
    voltage,
    length,
    locationKm,
    locationPercent,
    baseCurrent,
    totalPu,
    faultCurrent,
    faultMva,
    puVoltage,
    xrRatio,
    severity,
    devices: ranked,
    primary,
    backup,
  };
}

function formatKA(amps) {
  return `${(amps / 1000).toFixed(2)} kA`;
}

function updateDiagram(result) {
  const x = 120 + (670 * result.locationPercent) / 100;
  output.faultGroup.setAttribute("transform", `translate(${x - 640} 0)`);
  output.faultLabel.setAttribute("x", Math.max(530, Math.min(720, x - 42)));
  output.faultLabel.textContent = `Fault ${result.locationKm.toFixed(2)} km`;
  output.locationKm.textContent = `${result.locationKm.toFixed(2)} km`;
}

function updateResults(result) {
  output.faultCurrent.textContent = formatKA(result.faultCurrent);
  output.puVoltage.textContent = `${result.puVoltage.toFixed(3)} pu`;
  output.faultMva.textContent = `${result.faultMva.toFixed(2)} MVA`;
  output.xrRatio.textContent = result.xrRatio > 100 ? ">100" : result.xrRatio.toFixed(2);
  output.severityBadge.textContent = result.severity;
  output.severityBadge.className = result.severity;
  output.primaryDevice.textContent = `Operate ${result.primary.name}`;
  output.tripSummary.textContent = `Primary clearing in ${result.primary.tripTime.toFixed(2)} s`;
  output.baseCurrent.textContent = `${result.baseCurrent.toFixed(2)} A`;
  output.totalPu.textContent = `${result.totalPu.toFixed(3)} pu`;
  output.backupDevice.textContent = `${result.backup.name} (${result.backup.tripTime.toFixed(2)} s)`;

  output.deviceRows.innerHTML = result.devices
    .map(
      (device, index) => `
        <tr>
          <td>${index + 1}</td>
          <td>${device.name}</td>
          <td>${device.tripTime.toFixed(2)} s</td>
        </tr>
      `,
    )
    .join("");
}

function drawChart(result) {
  const canvas = output.chart;
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || canvas.width;
  const height = 310;
  canvas.width = width * ratio;
  canvas.height = height * ratio;
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);

  const plot = { x: 58, y: 18, w: width - 92, h: height - 66 };
  const minA = 100;
  const maxA = 100000;
  const minT = 0.01;
  const maxT = 100;
  const log = (value) => Math.log10(value);
  const xFor = (amps) => plot.x + ((log(amps) - log(minA)) / (log(maxA) - log(minA))) * plot.w;
  const yFor = (seconds) => plot.y + (1 - (log(seconds) - log(minT)) / (log(maxT) - log(minT))) * plot.h;

  ctx.strokeStyle = "#d9e1ec";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#627184";
  ctx.font = "12px Inter, sans-serif";
  [100, 1000, 10000, 100000].forEach((tick) => {
    const x = xFor(tick);
    ctx.beginPath();
    ctx.moveTo(x, plot.y);
    ctx.lineTo(x, plot.y + plot.h);
    ctx.stroke();
    ctx.fillText(tick >= 1000 ? `${tick / 1000}k` : `${tick}`, x - 8, plot.y + plot.h + 22);
  });
  [0.01, 0.1, 1, 10, 100].forEach((tick) => {
    const y = yFor(tick);
    ctx.beginPath();
    ctx.moveTo(plot.x, y);
    ctx.lineTo(plot.x + plot.w, y);
    ctx.stroke();
    ctx.fillText(`${tick}`, 12, y + 4);
  });

  ctx.strokeStyle = "#102033";
  ctx.beginPath();
  ctx.rect(plot.x, plot.y, plot.w, plot.h);
  ctx.stroke();

  const colors = ["#168a45", "#e66a00", "#1266d6", "#6941c6"];
  devices(result.length, number("relayPickup")).forEach((device, index) => {
    ctx.strokeStyle = colors[index];
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let amps = Math.max(device.pickup * 1.02, minA); amps <= maxA; amps *= 1.06) {
      const t = inverseTime(amps, device.pickup, device.dial);
      const x = xFor(amps);
      const y = yFor(Math.max(minT, Math.min(maxT, t)));
      if (amps === Math.max(device.pickup * 1.02, minA)) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.fillStyle = colors[index];
    ctx.fillText(device.name, plot.x + plot.w - 125, plot.y + 24 + index * 20);
  });

  const faultX = xFor(Math.max(minA, Math.min(maxA, result.faultCurrent)));
  ctx.strokeStyle = "#d92d20";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(faultX, plot.y);
  ctx.lineTo(faultX, plot.y + plot.h);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#d92d20";
  ctx.fillText(`If = ${formatKA(result.faultCurrent)}`, faultX + 8, plot.y + 18);
}

function render() {
  const result = calculate();
  updateDiagram(result);
  updateResults(result);
  drawChart(result);
}

Object.values(elements).forEach((element) => element.addEventListener("input", render));
document.getElementById("resetBtn").addEventListener("click", () => {
  Object.entries(defaults).forEach(([id, value]) => {
    elements[id].value = value;
  });
  render();
});

document.getElementById("labelsToggle").addEventListener("change", (event) => {
  document.querySelector(".diagram-labels").style.display = event.target.checked ? "block" : "none";
});

window.addEventListener("resize", render);
render();
