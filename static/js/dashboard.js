"use strict";
async function refreshDashboard() {
  const [summary, vms] = await Promise.all([Monitor.get("/api/dashboard"), Monitor.get("/api/vms")]);
  for (const id of ["total_vms","online_vms","offline_vms","active_alerts"]) {
    document.getElementById(id).textContent = summary[id];
  }
  document.getElementById("updated-at").textContent = new Date().toLocaleTimeString();
  document.getElementById("vm-grid").innerHTML = vms.length ? vms.map(vm => {
    const metric = vm.metrics;
    const resources = [["cpu_usage","CPU"],["memory_usage","RAM"],["disk_usage","Disk"]].map(([key,label]) => {
      const value = metric[key];
      const high = value > summary.thresholds[key];
      return '<div class="resource"><div class="d-flex justify-content-between"><span>' + label +
        '</span><strong>' + value.toFixed(1) + '%</strong></div><div class="progress" role="progressbar" aria-label="' +
        label + '" aria-valuenow="' + value + '" aria-valuemin="0" aria-valuemax="100"><div class="progress-bar ' +
        (high ? "bg-danger" : "") + '" style="width:' + value + '%"></div></div></div>';
    }).join("");
    return '<div class="col-12 col-md-6 col-lg-4"><article class="vm-card ' + vm.status +
      '"><div class="d-flex justify-content-between gap-2"><h3><a href="/vms/' + encodeURIComponent(vm.hostname) + '">' +
      Monitor.escape(vm.hostname) + '</a></h3>' + Monitor.badge(vm.status) +
      '</div><div class="text-secondary small">' + Monitor.escape(vm.ip_address) + '</div>' + resources +
      '<div class="card-footer-line d-flex justify-content-between gap-2"><span>Uptime ' + Monitor.uptime(metric.uptime) +
      '</span><span>' + (vm.status === "offline" ? "Last known values" : "Receiving metrics") + '</span></div></article></div>';
  }).join("") : '<div class="col-12"><div class="empty-state"><h2>No virtual machines yet</h2><p>Start an agent or the demo generator to see your first metrics.</p><code>python demo_generator.py</code></div></div>';
}
Monitor.poll(refreshDashboard);
