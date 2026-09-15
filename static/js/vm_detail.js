"use strict";
const hostname = document.getElementById("vm-detail").dataset.hostname;
const charts = {};
function networkRates(history) {
  return history.map((sample, index) => {
    if (!index) return {sent: null, received: null};
    const previous = history[index-1];
    const elapsed = sample.timestamp - previous.timestamp;
    if (elapsed <= 0 || sample.uptime < previous.uptime) return {sent: null, received: null};
    return {
      sent: sample.network_sent >= previous.network_sent ? (sample.network_sent - previous.network_sent) / elapsed : null,
      received: sample.network_received >= previous.network_received ? (sample.network_received - previous.network_received) / elapsed : null
    };
  });
}
function drawChart(id, labels, datasets, percentage) {
  if (charts[id]) {
    charts[id].data.labels = labels;
    charts[id].data.datasets.forEach((series, i) => { series.data = datasets[i].data; });
    charts[id].update("none");
    return;
  }
  charts[id] = new Chart(document.getElementById(id + "-chart"), {
    type: "line",
    data: {labels, datasets: datasets.map(series => ({
      ...series, borderWidth: 2, pointRadius: 0, pointHitRadius: 8, tension: 0.2, spanGaps: false
    }))},
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: {mode: "index", intersect: false},
      plugins: {legend: {display: !percentage}},
      scales: {
        y: {min: 0, ...(percentage ? {max: 100} : {}),
          title: {display: true, text: percentage ? "Usage (%)" : "Bytes / second"}},
        x: {ticks: {maxTicksLimit: 5, maxRotation: 0}, grid: {display: false}}
      }
    }
  });
}
async function refreshDetail() {
  const minutes = document.getElementById("history-window").value;
  const path = "/api/vms/" + encodeURIComponent(hostname);
  const [vm, history] = await Promise.all([Monitor.get(path), Monitor.get(path + "/history?minutes=" + minutes)]);
  document.getElementById("vm-status").innerHTML = Monitor.badge(vm.status);
  document.getElementById("vm-meta").textContent = vm.ip_address + " · Last received " + Monitor.date(vm.last_seen) +
    (vm.status === "offline" ? " · Showing last known values" : "");
  const m = vm.metrics;
  const readings = [
    ["CPU", m.cpu_usage.toFixed(1) + "%"],
    ["RAM", m.memory_usage.toFixed(1) + "%", Monitor.bytes(m.memory_used) + " / " + Monitor.bytes(m.memory_total)],
    ["Disk", m.disk_usage.toFixed(1) + "%", Monitor.bytes(m.disk_used) + " / " + Monitor.bytes(m.disk_total)],
    ["Network sent", Monitor.bytes(m.network_sent), "Cumulative counter"],
    ["Network received", Monitor.bytes(m.network_received), "Cumulative counter"],
    ["Uptime", Monitor.uptime(m.uptime)]
  ];
  document.getElementById("vm-readings").innerHTML = readings.map(([label,value,note]) =>
    '<div class="col-6 col-lg-4"><div class="summary-card h-100"><div class="text-secondary">' + label +
    '</div><div class="reading-value">' + value + '</div><div class="small text-secondary mt-1">' +
    (note || "&nbsp;") + '</div></div></div>').join("");
  document.getElementById("history-message").textContent = history.length ?
    history.length + " samples in this window. Network rates need two samples; counter resets appear as gaps." :
    "No samples in this time window. Waiting for new metrics.";
  const labels = history.map(sample => new Date(sample.timestamp * 1000).toLocaleTimeString());
  for (const [id, field, label, color] of [
    ["cpu","cpu_usage","CPU","#087f83"], ["memory","memory_usage","RAM","#5964c4"],
    ["disk","disk_usage","Disk","#c98424"]
  ]) drawChart(id, labels, [{label, data: history.map(sample => sample[field]), borderColor: color}], true);
  const rates = networkRates(history);
  drawChart("network", labels, [
    {label: "Sent", data: rates.map(rate => rate.sent), borderColor: "#087f83"},
    {label: "Received", data: rates.map(rate => rate.received), borderColor: "#5964c4"}
  ], false);
}
let detailRequest = Promise.resolve();
function loadDetail() {
  detailRequest = detailRequest.catch(() => {}).then(refreshDetail);
  return detailRequest;
}
document.getElementById("history-window").addEventListener("change", () => loadDetail().catch(Monitor.error));
Monitor.poll(loadDetail);
