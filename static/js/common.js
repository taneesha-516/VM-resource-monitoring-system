"use strict";
const Monitor = {
  escape(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    }[char]));
  },
  async get(path) {
    const response = await fetch(path, {cache: "no-store"});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.error || "Server returned " + response.status);
    }
    return response.json();
  },
  date(seconds) { return new Date(seconds * 1000).toLocaleString(); },
  bytes(value) {
    if (value == null) return "Not reported";
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let index = 0;
    while (value >= 1024 && index < units.length - 1) { value /= 1024; index++; }
    return value.toFixed(index ? 1 : 0) + " " + units[index];
  },
  uptime(seconds) {
    return Math.floor(seconds / 86400) + "d " + Math.floor(seconds % 86400 / 3600) +
      "h " + Math.floor(seconds % 3600 / 60) + "m";
  },
  badge(status) {
    const colors = {online:"success", offline:"danger", warning:"warning", critical:"danger", active:"danger", resolved:"secondary"};
    return '<span class="badge text-bg-' + (colors[status] || "secondary") + '">' +
      Monitor.escape(status.toUpperCase()) + "</span>";
  },
  error(error) {
    const node = document.getElementById("connection-error");
    node.textContent = error ? "Unable to refresh: " + error.message + " Displayed data may be stale." : "";
    node.classList.toggle("d-none", !error);
  },
  poll(callback) {
    const seconds = Number(document.body.dataset.refresh) || 5;
    async function tick() {
      try { await callback(); Monitor.error(null); }
      catch (error) { Monitor.error(error); }
      setTimeout(tick, seconds * 1000);
    }
    tick();
  }
};
