import json
import urllib.parse
import urllib.request
from pathlib import Path


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OUTPUT_FILE = Path("data/kinshasa_osm_features.json")

# Zone pilote approximative couvrant le cœur urbain de Kinshasa.
# On pourra ensuite l'ajuster ou travailler par commune.
SOUTH = -4.55
WEST = 15.15
NORTH = -4.15
EAST = 15.55


query = f"""
[out:json][timeout:120];
(
  node["highway"="traffic_signals"]
    ({SOUTH},{WEST},{NORTH},{EAST});

  way["junction"="roundabout"]
    ({SOUTH},{WEST},{NORTH},{EAST});
);
out center tags;
"""


def fetch_osm_data():
    print("KinTraffic - récupération des données OpenStreetMap...")
    print()

    data = urllib.parse.urlencode(
        {
            "data": query
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={
            "User-Agent": (
                "KinTraffic/0.5 "
                "(educational urban mobility prototype)"
            )
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=180
    ) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result


def normalize_element(element):
    tags = element.get("tags", {})

    if element["type"] == "node":
        latitude = element.get("lat")
        longitude = element.get("lon")

    else:
        center = element.get("center", {})
        latitude = center.get("lat")
        longitude = center.get("lon")

    if tags.get("highway") == "traffic_signals":
        feature_type = "traffic_signal"

    elif tags.get("junction") == "roundabout":
        feature_type = "roundabout"

    else:
        feature_type = "other"

    name = (
        tags.get("name")
        or tags.get("name:fr")
        or tags.get("ref")
    )

    if not name:
        if feature_type == "traffic_signal":
            name = f"Feu OSM {element['id']}"

        elif feature_type == "roundabout":
            name = f"Rond-point OSM {element['id']}"

        else:
            name = f"Point OSM {element['id']}"

    return {
        "osm_type": element["type"],
        "osm_id": element["id"],
        "feature_type": feature_type,
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "tags": tags,
    }


def main():
    result = fetch_osm_data()

    features = []

    for element in result.get(
        "elements",
        []
    ):
        feature = normalize_element(element)

        if (
            feature["latitude"] is not None
            and feature["longitude"] is not None
        ):
            features.append(feature)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            features,
            file,
            ensure_ascii=False,
            indent=2,
        )

    signals = sum(
        1
        for feature in features
        if feature["feature_type"]
        == "traffic_signal"
    )

    roundabouts = sum(
        1
        for feature in features
        if feature["feature_type"]
        == "roundabout"
    )

    print("Téléchargement terminé.")
    print()
    print(
        f"Total : {len(features)}"
    )
    print(
        f"Feux : {signals}"
    )
    print(
        f"Ronds-points : {roundabouts}"
    )
    print()
    print(
        f"Fichier : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()