# Complete project folder tree

Generated environments, caches and SQLite temporary WAL files are omitted.

```text
VM Resource monitoring and alert system/
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── agent_config.json
│   └── requirements.txt
├── database/
│   ├── .gitkeep
│   └── monitoring.db
├── docs/
│   ├── DEVELOPMENT_LOG.md
│   ├── FOLDER_TREE.md
│   └── VERIFICATION.md
├── models/
│   ├── __init__.py
│   ├── alert.py
│   ├── db.py
│   ├── metric.py
│   └── vm.py
├── routes/
│   ├── __init__.py
│   ├── api.py
│   └── views.py
├── services/
│   ├── __init__.py
│   ├── alerts.py
│   ├── monitoring.py
│   └── validation.py
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── alerts.js
│   │   ├── common.js
│   │   ├── dashboard.js
│   │   └── vm_detail.js
│   └── vendor/
│       ├── bootstrap.LICENSE
│       ├── bootstrap.min.css
│       ├── chart.umd.js
│       ├── chartjs.LICENSE
│       └── NOTICE.md
├── templates/
│   ├── about.html
│   ├── alerts.html
│   ├── base.html
│   ├── dashboard.html
│   └── vm_detail.html
├── tests/
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_api.py
│   ├── test_monitoring.py
│   └── test_network_rates.cjs
├── .gitignore
├── app.py
├── config.py
├── demo_generator.py
├── DEMO_SCRIPT.md
├── PROJECT_REPORT_NOTES.md
├── pytest.ini
├── README.md
├── requirements.txt
└── VIVA_NOTES.md
```
