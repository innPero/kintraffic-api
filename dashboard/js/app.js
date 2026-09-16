const API_BASE = window.location.origin;


const state = {
    features: [],
    traffic: [],
    incidents: [],
    trafficLights: [],
    intersections: new Map(),
    analytics: {},
    hasFittedMap: false,
};


const elements = {
    errorBanner:
        document.getElementById("errorBanner"),

    systemStatus:
        document.getElementById("systemStatus"),

    systemStatusText:
        document.getElementById(
            "systemStatusText"
        ),

    refreshButton:
        document.getElementById(
            "refreshButton"
        ),

    lastUpdate:
        document.getElementById(
            "lastUpdate"
        ),

    metricOsm:
        document.getElementById(
            "metricOsm"
        ),

    metricSignals:
        document.getElementById(
            "metricSignals"
        ),

    metricRoundabouts:
        document.getElementById(
            "metricRoundabouts"
        ),

    metricObservations:
        document.getElementById(
            "metricObservations"
        ),

    metricIncidents:
        document.getElementById(
            "metricIncidents"
        ),

    metricSpeed:
        document.getElementById(
            "metricSpeed"
        ),

    apiState:
        document.getElementById(
            "apiState"
        ),

    databaseState:
        document.getElementById(
            "databaseState"
        ),

    registeredLights:
        document.getElementById(
            "registeredLights"
        ),

    registeredIntersections:
        document.getElementById(
            "registeredIntersections"
        ),

    incidentList:
        document.getElementById(
            "incidentList"
        ),

    trafficTable:
        document.getElementById(
            "trafficTable"
        ),

    trafficLightList:
        document.getElementById(
            "trafficLightList"
        ),

    mapSearch:
        document.getElementById(
            "mapSearch"
        ),

    filterSignals:
        document.getElementById(
            "filterSignals"
        ),

    filterRoundabouts:
        document.getElementById(
            "filterRoundabouts"
        ),
};


const map = L.map(
    "map",
    {
        zoomControl: false,
    }
).setView(
    [-4.325, 15.322],
    12
);


L.control.zoom(
    {
        position: "bottomright",
    }
).addTo(map);


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,

        attribution:
            "&copy; OpenStreetMap contributors",
    }
).addTo(map);


const markerLayer = L.layerGroup()
    .addTo(map);


function escapeHTML(value) {
    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatNumber(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "--";
    }

    return new Intl.NumberFormat(
        "fr-FR"
    ).format(number);
}


function formatDate(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return "--";
    }

    return date.toLocaleString(
        "fr-FR",
        {
            dateStyle: "short",
            timeStyle: "short",
        }
    );
}


function humanize(value) {
    return String(
        value ?? ""
    )
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            character =>
                character.toUpperCase()
        );
}


function setSystemStatus(
    type,
    text
) {
    elements.systemStatus.classList.remove(
        "online",
        "offline",
        "loading"
    );

    elements.systemStatus.classList.add(
        type
    );

    elements.systemStatusText.textContent =
        text;
}


function showError(message) {
    elements.errorBanner.textContent =
        message;

    elements.errorBanner.classList.remove(
        "hidden"
    );
}


function hideError() {
    elements.errorBanner.classList.add(
        "hidden"
    );
}


async function fetchJSON(path) {
    const response = await fetch(
        `${API_BASE}${path}`,
        {
            cache: "no-store",
        }
    );

    if (!response.ok) {
        throw new Error(
            `${path}: HTTP ${response.status}`
        );
    }

    return response.json();
}


function getIntersectionName(id) {
    return (
        state.intersections.get(
            Number(id)
        )?.name
        ||
        `Carrefour #${id}`
    );
}


function renderMetrics() {
    const data = state.analytics;

    elements.metricOsm.textContent =
        formatNumber(
            data.osm_features
            ?? state.features.length
        );

    const signals =
        data.traffic_signals
        ??
        state.features.filter(
            item =>
                item.feature_type
                === "traffic_signal"
        ).length;

    const roundabouts =
        data.roundabouts
        ??
        state.features.filter(
            item =>
                item.feature_type
                === "roundabout"
        ).length;

    elements.metricSignals.textContent =
        formatNumber(signals);

    elements.metricRoundabouts.textContent =
        formatNumber(roundabouts);

    elements.metricObservations.textContent =
        formatNumber(
            data.traffic_observations
            ?? state.traffic.length
        );

    elements.metricIncidents.textContent =
        formatNumber(
            data.active_incidents
            ?? 0
        );

    elements.metricSpeed.textContent =
        data.average_speed == null
            ? "--"
            : `${data.average_speed} km/h`;

    elements.registeredLights.textContent =
        formatNumber(
            data.traffic_lights
            ?? state.trafficLights.length
        );

    elements.registeredIntersections.textContent =
        formatNumber(
            data.intersections
            ?? state.intersections.size
        );
}


function markerStyle(feature) {
    if (
        feature.feature_type
        === "traffic_signal"
    ) {
        return {
            radius: 7,
            color: "#ff6577",
            weight: 2,
            fillColor: "#ff6577",
            fillOpacity: 0.8,
        };
    }

    if (
        feature.feature_type
        === "roundabout"
    ) {
        return {
            radius: 6,
            color: "#4b9eff",
            weight: 2,
            fillColor: "#4b9eff",
            fillOpacity: 0.65,
        };
    }

    return {
        radius: 5,
        color: "#f6c85f",
        weight: 2,
        fillColor: "#f6c85f",
        fillOpacity: 0.7,
    };
}


function getFilteredFeatures() {
    const query =
        elements.mapSearch.value
            .trim()
            .toLowerCase();

    const showSignals =
        elements.filterSignals.checked;

    const showRoundabouts =
        elements.filterRoundabouts.checked;

    return state.features.filter(
        feature => {

            if (
                feature.feature_type
                === "traffic_signal"
                &&
                !showSignals
            ) {
                return false;
            }

            if (
                feature.feature_type
                === "roundabout"
                &&
                !showRoundabouts
            ) {
                return false;
            }

            if (query) {
                const haystack =
                    `${feature.name} ${feature.feature_type}`
                        .toLowerCase();

                if (
                    !haystack.includes(
                        query
                    )
                ) {
                    return false;
                }
            }

            return true;
        }
    );
}


function renderMap() {
    markerLayer.clearLayers();

    const features =
        getFilteredFeatures();

    const bounds = [];


    for (
        const feature
        of features
    ) {

        const latitude =
            Number(
                feature.latitude
            );

        const longitude =
            Number(
                feature.longitude
            );

        if (
            !Number.isFinite(latitude)
            ||
            !Number.isFinite(longitude)
        ) {
            continue;
        }


        const marker =
            L.circleMarker(
                [
                    latitude,
                    longitude,
                ],
                markerStyle(feature)
            );


        const typeLabel =
            feature.feature_type
            === "traffic_signal"
                ? "Feu de signalisation"
                : feature.feature_type
                    === "roundabout"
                    ? "Rond-point"
                    : humanize(
                        feature.feature_type
                    );


        marker.bindPopup(
            `
            <div class="map-popup">

                <h4>
                    ${escapeHTML(
                        feature.name
                    )}
                </h4>

                <p>
                    ${escapeHTML(
                        typeLabel
                    )}
                </p>

                <p>
                    OSM :
                    ${escapeHTML(
                        feature.osm_type
                    )}
                    #${escapeHTML(
                        feature.osm_id
                    )}
                </p>

                <p>
                    ${latitude.toFixed(6)},
                    ${longitude.toFixed(6)}
                </p>

            </div>
            `
        );


        marker.addTo(
            markerLayer
        );

        bounds.push(
            [
                latitude,
                longitude,
            ]
        );
    }


    if (
        !state.hasFittedMap
        &&
        bounds.length > 0
    ) {
        map.fitBounds(
            bounds,
            {
                padding: [25, 25],
            }
        );

        state.hasFittedMap = true;
    }
}


function renderTraffic() {
    if (
        state.traffic.length
        === 0
    ) {
        elements.trafficTable.innerHTML =
            `
            <tr>
                <td colspan="5">
                    Aucune observation trafic.
                </td>
            </tr>
            `;

        return;
    }


    const rows =
        state.traffic
            .slice(0, 12)
            .map(
                item => {

                    const congestion =
                        item.congestion_level
                        || "unknown";

                    return `
                    <tr>

                        <td>
                            ${escapeHTML(
                                getIntersectionName(
                                    item.intersection_id
                                )
                            )}
                        </td>

                        <td>
                            ${formatNumber(
                                item.vehicle_count
                            )}
                        </td>

                        <td>
                            ${escapeHTML(
                                item.average_speed
                            )}
                            km/h
                        </td>

                        <td>
                            <span
                                class="badge ${escapeHTML(
                                    congestion
                                )}"
                            >
                                ${escapeHTML(
                                    humanize(
                                        congestion
                                    )
                                )}
                            </span>
                        </td>

                        <td>
                            ${escapeHTML(
                                formatDate(
                                    item.timestamp
                                )
                            )}
                        </td>

                    </tr>
                    `;
                }
            )
            .join("");


    elements.trafficTable.innerHTML =
        rows;
}


function renderIncidents() {
    const incidents =
        state.incidents
            .slice(0, 6);


    if (
        incidents.length
        === 0
    ) {
        elements.incidentList.innerHTML =
            `
            <div class="empty-state">
                Aucun incident signalé.
            </div>
            `;

        return;
    }


    elements.incidentList.innerHTML =
        incidents
            .map(
                incident => {

                    return `
                    <div class="list-item">

                        <div class="list-item-top">

                            <strong>
                                ${escapeHTML(
                                    humanize(
                                        incident.type
                                    )
                                )}
                            </strong>

                            <span
                                class="badge ${escapeHTML(
                                    incident.severity
                                )}"
                            >
                                ${escapeHTML(
                                    incident.severity
                                )}
                            </span>

                        </div>

                        <p>
                            ${escapeHTML(
                                getIntersectionName(
                                    incident.intersection_id
                                )
                            )}
                        </p>

                        <p>
                            ${escapeHTML(
                                incident.description
                                || "Aucune description"
                            )}
                        </p>

                        <p>
                            État :
                            ${escapeHTML(
                                humanize(
                                    incident.status
                                )
                            )}
                        </p>

                    </div>
                    `;
                }
            )
            .join("");
}


function renderTrafficLights() {
    if (
        state.trafficLights.length
        === 0
    ) {
        elements.trafficLightList.innerHTML =
            `
            <div class="empty-state">
                Aucun contrôleur de feu
                enregistré pour le moment.
            </div>
            `;

        return;
    }


    elements.trafficLightList.innerHTML =
        state.trafficLights
            .slice(0, 8)
            .map(
                light => {

                    return `
                    <div class="list-item">

                        <div class="list-item-top">

                            <strong>
                                ${escapeHTML(
                                    getIntersectionName(
                                        light.intersection_id
                                    )
                                )}
                            </strong>

                            <span
                                class="badge ${escapeHTML(
                                    light.status
                                )}"
                            >
                                ${escapeHTML(
                                    light.status
                                )}
                            </span>

                        </div>

                        <p>
                            Phase :
                            ${escapeHTML(
                                humanize(
                                    light.current_phase
                                )
                            )}
                        </p>

                        <p>
                            Vert
                            ${escapeHTML(
                                light.green_duration
                            )}s
                            •
                            Jaune
                            ${escapeHTML(
                                light.yellow_duration
                            )}s
                            •
                            Rouge
                            ${escapeHTML(
                                light.red_duration
                            )}s
                        </p>

                    </div>
                    `;
                }
            )
            .join("");
}


async function loadDashboard() {
    hideError();

    setSystemStatus(
        "loading",
        "Synchronisation..."
    );

    elements.refreshButton.disabled =
        true;


    try {

        const [
            health,
            analytics,
            mapData,
            traffic,
            incidents,
            trafficLights,
            intersections,
        ] = await Promise.all(
            [
                fetchJSON(
                    "/health"
                ),

                fetchJSON(
                    "/analytics/summary"
                ),

                fetchJSON(
                    "/map/features"
                ),

                fetchJSON(
                    "/traffic"
                ),

                fetchJSON(
                    "/incidents"
                ),

                fetchJSON(
                    "/traffic-lights"
                ),

                fetchJSON(
                    "/intersections"
                ),
            ]
        );


        state.analytics =
            analytics || {};

        state.features =
            mapData.features || [];

        state.traffic =
            traffic || [];

        state.incidents =
            incidents || [];

        state.trafficLights =
            trafficLights || [];


        state.intersections =
            new Map(
                (intersections || [])
                    .map(
                        item => [
                            Number(
                                item.id
                            ),
                            item,
                        ]
                    )
            );


        elements.apiState.textContent =
            "En ligne";

        elements.databaseState.textContent =
            health.database
            === "connected"
                ? "Connectée"
                : humanize(
                    health.database
                );


        renderMetrics();
        renderMap();
        renderTraffic();
        renderIncidents();
        renderTrafficLights();


        elements.lastUpdate.textContent =
            new Date()
                .toLocaleString(
                    "fr-FR"
                );


        setSystemStatus(
            "online",
            "Système en ligne"
        );

    } catch (error) {

        console.error(error);

        elements.apiState.textContent =
            "Erreur";

        elements.databaseState.textContent =
            "Indisponible";

        setSystemStatus(
            "offline",
            "Connexion interrompue"
        );

        showError(
            "KinTraffic ne parvient pas à synchroniser toutes les données."
        );

    } finally {

        elements.refreshButton.disabled =
            false;
    }
}


elements.refreshButton
    .addEventListener(
        "click",
        loadDashboard
    );


elements.mapSearch
    .addEventListener(
        "input",
        renderMap
    );


elements.filterSignals
    .addEventListener(
        "change",
        renderMap
    );


elements.filterRoundabouts
    .addEventListener(
        "change",
        renderMap
    );


loadDashboard();


setInterval(
    loadDashboard,
    30000
);