from datetime import time

from app.core.database import SessionLocal
from app.models.location_db import LocationDB, LocationHourDB


LOCATIONS = [
    {
        "customer_name": "DIRTY RABBIT",
        "toast_name": "Los Perritos Del Barrio 3",
        "city": "WYNWOOD, MIAMI",
        "address": "151 NW 24TH ST, MIAMI, FL33127",
        "hours": [
            (0, time(17, 0), time(4, 0)),
            (1, time(17, 0), time(4, 0)),
            (2, time(17, 0), time(4, 0)),
            (3, time(17, 0), time(4, 0)),
            (4, time(17, 0), time(4, 0)),
            (5, time(17, 0), time(4, 0)),
            (6, time(17, 0), time(4, 0)),
        ],
    },
    {
        "customer_name": "WYNWOOD FOOD TRUCK",
        "toast_name": "Food Truck",
        "city": "WYNWOOD, MIAMI",
        "address": "2236 NW 1 ST CT, 33127",
        "hours": [
            (0, time(17, 0), time(2, 0)),
            (1, time(17, 0), time(2, 0)),
            (2, time(17, 0), time(2, 0)),
            (3, time(17, 0), time(4, 0)),
            (4, time(17, 0), time(4, 0)),
            (5, time(17, 0), time(4, 0)),
            (6, time(17, 0), time(4, 0)),
        ],
    },
    {
        "customer_name": "SUNRISE",
        "toast_name": "Los Perritos Del Barrio 4 - 3801 N UNIVERSITY DR",
        "city": "FOURT LAUDERDALE, FLORIDA",
        "address": "3801 N UNIVERSITY DR SUNRISE FL33351",
        "hours": [
            (0, time(15, 30), time(0, 0)),
            (1, time(15, 30), time(0, 0)),
            (2, time(15, 30), time(0, 0)),
            (3, time(13, 0), time(1, 0)),
            (4, time(13, 0), time(1, 0)),
            (5, time(13, 0), time(1, 0)),
            (6, time(13, 0), time(0, 0)),
        ],
    },
]


def seed_locations():
    db = SessionLocal()

    try:
        for location_data in LOCATIONS:
            existing = (
                db.query(LocationDB)
                .filter(
                    LocationDB.customer_name
                    == location_data["customer_name"]
                )
                .first()
            )

            if existing:
                continue

            location = LocationDB(
                customer_name=location_data["customer_name"],
                toast_name=location_data["toast_name"],
                city=location_data["city"],
                address=location_data["address"],
                toast_restaurant_guid=None,
                active=True,
            )

            db.add(location)
            db.flush()

            for day_of_week, opens_at, closes_at in location_data["hours"]:
                db.add(
                    LocationHourDB(
                        location_id=location.id,
                        day_of_week=day_of_week,
                        opens_at=opens_at,
                        closes_at=closes_at,
                    )
                )

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_locations()
    print("Sedes cargadas correctamente.")