import L from 'leaflet'
import './label.js'

// Fix Leaflet's default icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
    iconRetinaUrl: '/images/leaflet/marker-icon-2x.png',
    iconUrl: '/images/leaflet/marker-icon.png',
    shadowUrl: '/images/leaflet/marker-shadow.png'
})

// Initialise namespace with defaults (can be overridden by server-side templates)
if (typeof window.org === 'undefined') {
    window.org = {}
}
if (typeof window.org.woeplanet === 'undefined') {
    window.org.woeplanet = {}
}

const defaults = {
    bounds: null,
    centroid: null,
    zoom: 10,
    credits_url: '/credits',
    nullisland_url: '/geojson/null-island.geojson',
    popup: null,
    scale: null,
    placetype: null,
    geojson: null
}

Object.keys(defaults).forEach(key => {
    if (typeof window.org.woeplanet[key] === 'undefined') {
        window.org.woeplanet[key] = defaults[key]
    }
})

/**
 * Check if an object is empty
 */
function isEmptyObject(obj) {
    return obj === null || obj === undefined || Object.keys(obj).length === 0
}

/**
 * WoeplanetMap class - manages side and main map instances
 */
export class WoeplanetMap {
    constructor() {
        this.config = window.org.woeplanet
        this.maps = {
            side: undefined,
            main: undefined
        }
        this.ids = {
            side: 'side-map',
            main: 'main-map'
        }
        this.popup = undefined
        this.banner_height = 0
        this.banner_width = 0
        this.min_map_height = 415

        this.initSideMap()
        this.initMainMap()
    }

    initSideMap() {
        const sideMapEl = document.getElementById(this.ids.side)
        if (!sideMapEl) return

        const options = {
            attributionControl: false,
            zoomControl: false,
            doubleClickZoom: false,
            boxZoom: false,
            dragging: false,
            keyboard: false,
            scrollWheelZoom: false,
            touchZoom: false
        }

        this.maps.side = L.map(this.ids.side, options)
        L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}{r}.{ext}', {
            minZoom: 0,
            maxZoom: 20,
            ext: 'png'
        }).addTo(this.maps.side)

        const attribution = '<a href="' + this.config.credits_url + '">Map Credits</a>'
        L.control.attribution({
            prefix: attribution,
            position: 'bottomleft'
        }).addTo(this.maps.side)

        if (!isEmptyObject(this.config.bounds)) {
            this.maps.side.fitBounds(this.config.bounds)
        } else if (this.config.centroid) {
            this.maps.side.setView(this.config.centroid, this.config.zoom)
        } else {
            this.loadNullIsland(this.maps.side, 3)
        }
    }

    initMainMap() {
        const mainMapEl = document.getElementById(this.ids.main)
        if (!mainMapEl) return

        const options = {
            attributionControl: false
        }

        this.maps.main = L.map(this.ids.main, options)
        L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.{ext}', {
            minZoom: 0,
            maxZoom: 20,
            ext: 'png'
        }).addTo(this.maps.main)

        if (!isEmptyObject(this.config.bounds)) {
            this.maps.main.fitBounds(this.config.bounds)
            this.drawGeometry(this.maps.main)
            this.openPopup()
            this.syncMaps()
        } else if (this.config.centroid) {
            this.maps.main.setView(this.config.centroid, this.config.zoom)
            this.drawGeometry(this.maps.main)
            this.openPopup()
            this.syncMaps()
        } else {
            this.loadNullIsland(this.maps.main, 4, () => {
                this.openPopup()
                this.syncMaps()
            })
        }
    }

    drawGeometry(map) {
        if (isEmptyObject(this.config.geojson)) return

        const style = {
            color: '#6000DB',
            weight: 4,
            opacity: 1,
            fillColor: '#6000DB',
            fillOpacity: 0.35
        }

        try {
            L.geoJSON(this.config.geojson, { style }).addTo(map)
        } catch (error) {
            console.error('Failed to draw geometry:', error)
        }
    }

    async loadNullIsland(map, zoomOffset, callback) {
        const sideMapEl = document.getElementById(this.ids.side)
        if (sideMapEl && map === this.maps.side) {
            L.control.nullLabel({
                position: 'topleft'
            }).addTo(map)
        }

        try {
            const response = await fetch(this.config.nullisland_url)
            if (!response.ok) {
                throw new Error(`HTTP ${response.status} when fetching Null Island GeoJSON`)
            }
            const data = await response.json()

            const myStyle = {
                color: '#ff7800',
                weight: 5,
                opacity: 0.65
            }

            const layer = L.geoJSON(data, {
                style: myStyle
            }).addTo(map)

            const bounds = layer.getBounds()
            const point = bounds.getCenter()
            let zoom = map.getBoundsZoom(bounds, true)
            zoom += zoomOffset

            map.setView(point, zoom)

            if (callback) callback()
        } catch (error) {
            console.error('Failed to load Null Island GeoJSON:', error)
        }
    }

    openPopup() {
        const mainMapEl = document.getElementById(this.ids.main)
        if (mainMapEl && this.config.popup) {
            this.popup = L.popup({
                closeOnClick: false,
                closeButton: false
            })
                .setContent(this.config.popup)
                .setLatLng(this.maps.main.getCenter())
                .openOn(this.maps.main)
        }
    }

    syncMaps() {
        if (!isEmptyObject(this.maps.main) && !isEmptyObject(this.maps.side)) {
            this.maps.main.on('zoomend', this.syncHandler.bind(this))
            this.maps.main.on('moveend', this.syncHandler.bind(this))
        }
    }

    syncHandler(_event) {
        const pt = this.maps.main.getCenter()
        const zm = this.maps.side.getZoom()
        this.maps.side.setView(pt, zm)
    }
}

export function initMap() {
    if (document.getElementById('side-map') || document.getElementById('main-map')) {
        return new WoeplanetMap()
    }
    return null
}
