/**
 * Handles geolocation for the location page
 */

function getParameterByName(name, url = window.location.href) {
    const escapedName = name.replace(/[[\]]/g, '\\$&')
    const regex = new RegExp('[?&]' + escapedName + '(=([^&#]*)|&|#|$)')
    const results = regex.exec(url)
    if (!results) return null
    if (!results[2]) return ''
    return decodeURIComponent(results[2].replace(/\+/g, ' '))
}

function geoSuccess(position) {
    const askingEl = document.getElementById('location-asking')
    const successEl = document.getElementById('location-success')

    if (askingEl) askingEl.style.display = 'none'
    if (successEl) successEl.style.display = 'block'

    const params = new URLSearchParams({
        lat: position.coords.latitude,
        lng: position.coords.longitude
    })
    const redirectTo = window.location.href + '?' + params.toString()
    window.location.replace(redirectTo)
}

function geoError(error) {
    console.log('Error: navigator.geolocation.getCurrentPosition() failed')
    showLocationError(error.code + ': ' + error.message)
}

export function initLocation() {
    const locationEl = document.getElementById('location')
    if (!locationEl) return

    const lat = getParameterByName('lat')
    const lng = getParameterByName('lng')

    if (!lat && !lng) {
        if (!window.isSecureContext) {
            showLocationError('Geolocation requires a secure (HTTPS) connection')
            return
        }
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(geoSuccess, geoError)
        } else {
            showLocationError('Your browser does not support geolocation')
        }
    }
}

function showLocationError(message) {
    const statusEl = document.getElementById('location-status')
    const askingEl = document.getElementById('location-asking')
    const errorEl = document.getElementById('location-error')

    if (statusEl) statusEl.textContent = message
    if (askingEl) askingEl.style.display = 'none'
    if (errorEl) errorEl.style.display = 'block'
}
