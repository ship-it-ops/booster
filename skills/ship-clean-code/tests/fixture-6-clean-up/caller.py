"""Nightly order report."""
from orders.export import export_orders


def nightly_report(orders, out):
    out.write(export_orders(orders, hdr=True))


def cancelled_report(orders, out):
    out.write(export_orders(orders, include_cancelled=True, hdr=False))
