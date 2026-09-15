from flask import Blueprint, abort, render_template

from models.vm import find_vm

views = Blueprint("views", __name__)


@views.get("/")
@views.get("/vms")
def dashboard():
    return render_template("dashboard.html", title="Dashboard")


@views.get("/vms/<hostname>")
def vm_detail(hostname):
    if find_vm(hostname) is None:
        abort(404, description="VM not found.")
    return render_template("vm_detail.html", title=hostname, hostname=hostname)


@views.get("/alerts")
def alerts():
    return render_template("alerts.html", title="Alerts")


@views.get("/about")
def about():
    return render_template("about.html", title="About")
