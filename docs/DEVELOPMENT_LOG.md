# Development phases

| Phase | Important files | Verification |
| --- | --- | --- |
| 1. Structure and requirements | requirements.txt, config.py, package folders | Virtual environment created; dependencies installed after network permission |
| 2. Database models | models/db.py, vm.py, metric.py, alert.py | Modules compiled; all three SQLite tables initialized |
| 3. REST API | app.py, routes/api.py, services/validation.py | Registration, insertion, history and invalid-percentage smoke checks |
| 4. Monitoring agent | agent/agent.py, agent_config.json | Real local psutil sample validated; connection failure handled |
| 5. Dashboard | templates/, static/css/, dashboard.js, alerts.js | Four main pages rendered; scripts passed syntax checks |
| 6. Historical graphs | vm_detail.html, vm_detail.js | Chronological history and all windows checked; Chart.js served |
| 7. Alert rules | services/alerts.py | All three types, deduplication, exact-boundary recovery and new episodes checked |
| 8. Offline detection | services/monitoring.py | 30-second boundary, transition, deduplication and reconnection checked |
| 9. Demo generator | demo_generator.py | Both scenarios validated for all three VMs; counters increased |
| 10. Testing | tests/ | 38 pytest cases pass; Node rate checks and live browser checks pass |
| 11. Documentation | README.md, VIVA_NOTES.md, PROJECT_REPORT_NOTES.md, DEMO_SCRIPT.md | Commands and local references checked against the delivered implementation |

## Issues found and corrected

- pip and frontend downloads needed network permission in the development sandbox.
- A database smoke command initially used incompatible shell quoting; rerun successfully using a literal multiline Python script.
- Tests found that extremely large integers could overflow during finite-number validation. Bounds are now checked before float conversion.
- Tests found that the IP parser accepted integer inputs. Validation now explicitly requires a string.
- Detail-page badges inherited heading letter spacing; badge spacing was corrected.
- Full-page browser screenshot capture was unavailable in one attempt; normal viewport captures verified the charts and mobile layout.
