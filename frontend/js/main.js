/**
 * Main entry point for the WOEplanet Spelunker frontend
 */

import { initMap } from './map.js'
import { initLocation } from './location.js'
import { initResults } from './results.js'

document.addEventListener('DOMContentLoaded', () => {
    initMap()
    initLocation()
    initResults()
})
