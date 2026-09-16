import json
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.models import OSMFeature


DATA_FILE = Path(
    "data/kinshasa_osm_features.json"
)


def main():
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Fichier introuvable : {DATA_FILE}"
        )

    Base.metadata.create_all(
        bind=engine
    )

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        features = json.load(file)

    db = SessionLocal()

    created = 0
    updated = 0

    try:
        for feature in features:
            osm_key = (
                f"{feature['osm_type']}:"
                f"{feature['osm_id']}"
            )

            row = (
                db.query(OSMFeature)
                .filter(
                    OSMFeature.osm_key
                    == osm_key
                )
                .first()
            )

            if row is None:
                row = OSMFeature(
                    osm_key=osm_key
                )

                db.add(row)
                created += 1

            else:
                updated += 1

            row.osm_type = feature["osm_type"]
            row.osm_id = feature["osm_id"]
            row.feature_type = feature["feature_type"]
            row.name = feature["name"]
            row.latitude = feature["latitude"]
            row.longitude = feature["longitude"]
            row.tags = feature.get("tags", {})
            row.source = "OpenStreetMap"

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    print()
    print("Import OpenStreetMap terminé ✅")
    print(f"Nouveaux : {created}")
    print(f"Mis à jour : {updated}")
    print(f"Total traité : {len(features)}")


if __name__ == "__main__":
    main()
