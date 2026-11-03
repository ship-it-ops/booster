import os

import requests

PARTNER_URL = os.environ.get("PARTNER_URL", "https://api.partner.example")
PARTNER_KEY = os.environ["PARTNER_KEY"]


def fetch_account(account_id):
    response = requests.get(
        f"{PARTNER_URL}/accounts/{account_id}",
        headers={"Authorization": f"Bearer {PARTNER_KEY}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def push_order(order):
    response = requests.post(
        f"{PARTNER_URL}/orders",
        json=order,
        headers={"Authorization": f"Bearer {PARTNER_KEY}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["id"]
