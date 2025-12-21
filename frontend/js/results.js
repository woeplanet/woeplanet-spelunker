/**
 * Handles search results toggle
 */

export function initResults() {
    const searchInfoLink = document.querySelector('#search-info a')
    const searchQuery = document.getElementById('search-query')

    if (searchInfoLink && searchQuery) {
        searchInfoLink.addEventListener('click', (e) => {
            e.preventDefault()
            searchQuery.style.display = searchQuery.style.display === 'none' ? 'block' : 'none'
        })
    }
}
