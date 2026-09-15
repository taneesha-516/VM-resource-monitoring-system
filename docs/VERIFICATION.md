# Verification record

Verified on 15 September 2026 on a Windows host with Python 3.13.

## Automated checks

- Project virtual environment created; requirements installed successfully.
- SQLite schema initialized automatically.
- 38 pytest cases passed.
- Node syntax checks passed for all four application scripts.
- Additional Node checks passed for network-rate arithmetic, counter resets, reboots and zero intervals.
- Python source compilation passed.
- Tests use temporary databases; the demonstration database contains only locally generated demo samples.

## Live integration and browser checks

1. Started Flask with python app.py on port 5000.
2. Ran the three-VM generator with --scenario alerts --offline-after 20.
3. Confirmed all three identities appeared with CPU/RAM/disk readings.
4. Confirmed vm-03 stopped sending while the other two continued.
5. Confirmed dashboard showed two online VMs and one offline VM.
6. Confirmed threshold and offline alert rows, including resolved episodes.
7. Opened vm-01 and visually inspected CPU, RAM, disk and network charts with stored data.
8. Changed the history selector and confirmed the selected window.
9. Combined VM, Critical and Active alert filters and confirmed only matching rows.
10. Checked a 390-pixel-wide mobile dashboard.
11. Restarted normal simulation and observed automatic online recovery and zero active alerts without reloading the page.
12. Browser console contained no warning/error logs during the checked dashboard, detail and alerts flows.

## Environment boundaries

- No Ubuntu guest or VirtualBox network was created/configured during this build.
- Real psutil collection was tested on the Windows host; Ubuntu setup is documented for the student to perform.
- The documented Windows virtual-environment path was executed. Ubuntu apt/network setup requires an actual guest and is not claimed as executed.
- This is functional testing, not a production security review or load benchmark.
- The Flask server is a development server. Use the documented trusted local lab setup.
