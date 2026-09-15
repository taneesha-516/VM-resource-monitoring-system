"use strict";
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({
  document: {getElementById: () => ({dataset: {hostname: 'test'}, addEventListener() {}})},
  Monitor: {poll() {}}
});
vm.runInContext(fs.readFileSync('static/js/vm_detail.js', 'utf8'), context);
const calculate = samples => JSON.parse(vm.runInContext('JSON.stringify(networkRates(' + JSON.stringify(samples) + '))', context));
const first = {timestamp:10, uptime:100, network_sent:100, network_received:200};
const second = {timestamp:15, uptime:105, network_sent:200, network_received:400};
assert.deepEqual(calculate([first,second]), [{sent:null, received:null},{sent:20,received:40}]);
assert.deepEqual(calculate([first,{...second,network_sent:20}])[1], {sent:null,received:40});
assert.deepEqual(calculate([first,{...second,uptime:1}])[1], {sent:null,received:null});
assert.deepEqual(calculate([first,{...second,timestamp:10}])[1], {sent:null,received:null});
console.log('Network-rate calculation, counter reset, reboot and zero interval checks passed.');
