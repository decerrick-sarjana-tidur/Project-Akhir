"""data.py — seed vaults + plain-dict data model (mirrors seedVaults() in JSX)"""
import time


def seed_vaults():
    return [
        {
            "id": 1, "name": "iPhone 15 Pro", "category": "Gadget", "target": 18_000_000,
            "current": 9_800_000, "deadline": "2026-12-01", "priority": True,
            "itemLink": "https://www.apple.com/id/iphone-15-pro/",
            "history": [
                {"id": 1, "type": "tambah", "amount": 2_000_000, "date": "2026-03-10"},
                {"id": 2, "type": "tambah", "amount": 1_500_000, "date": "2026-04-12"},
                {"id": 3, "type": "tambah", "amount": 2_300_000, "date": "2026-05-18"},
                {"id": 4, "type": "tarik", "amount": 500_000, "date": "2026-06-02"},
                {"id": 5, "type": "tambah", "amount": 2_500_000, "date": "2026-07-20"},
                {"id": 6, "type": "tambah", "amount": 2_000_000, "date": "2026-08-15"},
            ],
        },
        {
            "id": 2, "name": "Liburan ke Bali", "category": "Liburan", "target": 6_000_000,
            "current": 4_650_000, "deadline": "2026-11-01", "priority": False, "itemLink": "",
            "history": [
                {"id": 1, "type": "tambah", "amount": 1_000_000, "date": "2026-04-05"},
                {"id": 2, "type": "tambah", "amount": 1_200_000, "date": "2026-05-05"},
                {"id": 3, "type": "tambah", "amount": 900_000, "date": "2026-06-10"},
                {"id": 4, "type": "tambah", "amount": 800_000, "date": "2026-07-10"},
                {"id": 5, "type": "tambah", "amount": 750_000, "date": "2026-08-08"},
            ],
        },
        {
            "id": 3, "name": "Dana Darurat", "category": "Darurat", "target": 15_000_000,
            "current": 15_000_000, "deadline": "2026-09-01", "priority": False, "itemLink": "",
            "history": [
                {"id": 1, "type": "tambah", "amount": 5_000_000, "date": "2026-03-01"},
                {"id": 2, "type": "tambah", "amount": 5_000_000, "date": "2026-05-01"},
                {"id": 3, "type": "tambah", "amount": 5_000_000, "date": "2026-07-01"},
            ],
        },
        {
            "id": 4, "name": "Kursus Desain UI/UX", "category": "Pendidikan", "target": 2_500_000,
            "current": 625_000, "deadline": "2027-01-15", "priority": False,
            "itemLink": "https://example.com/kursus-uiux",
            "history": [
                {"id": 1, "type": "tambah", "amount": 325_000, "date": "2026-07-01"},
                {"id": 2, "type": "tambah", "amount": 300_000, "date": "2026-08-20"},
            ],
        },
    ]


def new_id():
    return int(time.time() * 1000)
