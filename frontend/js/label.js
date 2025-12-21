import L from 'leaflet'

L.Control.NullLabel = L.Control.extend({
    onAdd: function (_map) {
        const text = L.DomUtil.create('div')
        text.id = 'null-island'
        text.className = 'text-panel'
        text.innerHTML = '<p><strong>Ahem.</strong></p><p>We don\'t seem to have coordinates for this place.</p><p>So here\'s a map of Null Island instead.</p>'
        return text
    },
    onRemove: function (_map) {}
})

L.control.nullLabel = function (opts) {
    return new L.Control.NullLabel(opts)
}

export default L.control.nullLabel
