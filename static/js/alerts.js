"use strict";
let offset = 0;
const pageSize = 25;
async function refreshAlerts() {
  const filters = new URLSearchParams({limit: pageSize, offset});
  for (const id of ["hostname","severity","status"]) {
    const value = document.getElementById(id).value;
    if (value) filters.set(id, value);
  }
  const [data, vms] = await Promise.all([Monitor.get("/api/alerts?" + filters), Monitor.get("/api/vms")]);
  const select = document.getElementById("hostname");
  const selected = select.value;
  select.innerHTML = '<option value="">All VMs</option>' + vms.map(vm =>
    '<option value="' + Monitor.escape(vm.hostname) + '">' + Monitor.escape(vm.hostname) + '</option>').join("");
  select.value = selected;
  document.getElementById("alert-rows").innerHTML = data.items.length ? data.items.map(alert => {
    const unit = alert.alert_type === "offline" ? "s" : "%";
    return "<tr><td><a href='/vms/" + encodeURIComponent(alert.hostname) + "'>" + Monitor.escape(alert.hostname) +
      '</a><div class="text-secondary small">' + Monitor.escape(alert.alert_type) + "</div></td><td>" +
      Monitor.badge(alert.severity) + "</td><td>" + Monitor.escape(alert.message) + "</td><td>" +
      alert.value.toFixed(1) + unit + " / " + alert.threshold + unit + "</td><td>" +
      Monitor.date(alert.timestamp) + "</td><td>" + Monitor.badge(alert.resolved ? "resolved" : "active") + "</td></tr>";
  }).join("") : '<tr><td colspan="6" class="text-center py-5 text-secondary">No alerts match these filters.</td></tr>';
  document.getElementById("alert-count").textContent = data.total ?
    (offset + 1) + "–" + (offset + data.items.length) + " of " + data.total + " alerts" : "0 alerts";
  document.getElementById("previous").disabled = offset === 0;
  document.getElementById("next").disabled = offset + pageSize >= data.total;
}
let alertRequest = Promise.resolve();
function loadAlerts() {
  alertRequest = alertRequest.catch(() => {}).then(refreshAlerts);
  return alertRequest;
}
document.getElementById("filters").addEventListener("submit", event => event.preventDefault());
document.getElementById("filters").addEventListener("change", () => { offset = 0; loadAlerts().catch(Monitor.error); });
document.getElementById("previous").addEventListener("click", () => { offset = Math.max(0, offset-pageSize); loadAlerts().catch(Monitor.error); });
document.getElementById("next").addEventListener("click", () => { offset += pageSize; loadAlerts().catch(Monitor.error); });
Monitor.poll(loadAlerts);
