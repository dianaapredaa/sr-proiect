/**
 * CineMatch - Movie Recommendation System
 * Main JavaScript File
 */

// Global state
const AppState = {
    userId: null,
    preferredGenres: [],
    isNewUser: true
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
async function initializeApp() {
    try {
        await loadUserPreferences();
        updateUIForUserStatus();
    } catch (error) {
        console.error('Error initializing app:', error);
    }
}

/**
 * Load user preferences from the server
 */
async function loadUserPreferences() {
    try {
        const response = await fetch('/api/user/preferences');
        const data = await response.json();
        
        AppState.userId = data.user_id;
        AppState.preferredGenres = data.preferred_genres || [];
        AppState.isNewUser = data.is_new_user;
        
        return data;
    } catch (error) {
        console.error('Error loading user preferences:', error);
        return null;
    }
}

/**
 * Update UI based on user status (new user vs returning user)
 */
function updateUIForUserStatus() {
    const userStatus = document.getElementById('userStatus');
    
    if (userStatus) {
        if (AppState.isNewUser) {
            userStatus.textContent = 'Utilizator Nou';
        } else {
            userStatus.textContent = 'Utilizator Activ';
        }
    }
}

/**
 * API Helper Functions
 */
const API = {
    /**
     * Get personalized recommendations
     */
    async getRecommendations(options = {}) {
        const params = new URLSearchParams();
        
        if (options.count) params.append('count', options.count);
        if (options.genres) params.append('genres', options.genres.join(','));
        if (AppState.userId) params.append('user_id', AppState.userId);
        
        const response = await fetch(`/api/recommendations?${params}`);
        return response.json();
    },
    
    /**
     * Get similar movies
     */
    async getSimilarMovies(movieId, count = 6) {
        const response = await fetch(`/api/similar/${movieId}?count=${count}`);
        return response.json();
    },
    
    /**
     * Submit a rating
     */
    async submitRating(movieId, rating) {
        const response = await fetch('/api/rate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                movie_id: movieId,
                rating: rating,
                user_id: AppState.userId
            })
        });
        return response.json();
    },
    
    /**
     * Get movie details
     */
    async getMovieDetails(movieId) {
        const response = await fetch(`/api/movie/${movieId}`);
        return response.json();
    },
    
    /**
     * Get popular movies
     */
    async getPopularMovies(count = 10) {
        const response = await fetch(`/api/popular?count=${count}`);
        return response.json();
    },
    
    /**
     * Register user with preferences
     */
    async registerUser(preferredGenres, preferredDirectors = []) {
        const response = await fetch('/api/user/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                preferred_genres: preferredGenres,
                preferred_directors: preferredDirectors
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            AppState.userId = data.user_id;
            AppState.preferredGenres = preferredGenres;
            AppState.isNewUser = false;
        }
        
        return data;
    }
};

/**
 * UI Helper Functions
 */
const UI = {
    /**
     * Create a movie card element
     */
    createMovieCard(movie, index = 0) {
        const posterUrl = movie.poster_path 
            ? `https://image.tmdb.org/t/p/w342${movie.poster_path}`
            : 'https://via.placeholder.com/342x513/1a1a2e/eee?text=No+Poster';
        
        const genres = Array.isArray(movie.genres) 
            ? movie.genres.slice(0, 3).join(', ')
            : movie.genres_str || '';
        
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.style.animationDelay = `${index * 0.05}s`;
        
        card.innerHTML = `
            <div class="movie-poster">
                <img src="${posterUrl}" alt="${movie.title}" loading="lazy">
                <div class="movie-overlay">
                    <div class="rating-badge">
                        <span class="star">★</span>
                        <span class="score">${movie.vote_average?.toFixed(1) || 'N/A'}</span>
                    </div>
                    <button class="btn-view" onclick="UI.viewMovie('${movie.id}')">
                        Vezi Detalii
                    </button>
                </div>
            </div>
            <div class="movie-info">
                <h3 class="movie-title">${movie.title}</h3>
                <p class="movie-genres">${genres}</p>
                <div class="movie-rating">
                    <div class="rating-stars">
                        ${this.generateStars(movie.vote_average || 0)}
                    </div>
                    <span class="vote-count">(${movie.vote_count?.toLocaleString() || 0})</span>
                </div>
            </div>
        `;
        
        return card;
    },
    
    /**
     * Create a carousel card element
     */
    createCarouselCard(movie, index = 0) {
        const posterUrl = movie.poster_path 
            ? `https://image.tmdb.org/t/p/w185${movie.poster_path}`
            : 'https://via.placeholder.com/185x278/1a1a2e/eee?text=No+Poster';
        
        const card = document.createElement('div');
        card.className = 'carousel-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        card.innerHTML = `
            <img src="${posterUrl}" alt="${movie.title}" loading="lazy">
            <div class="carousel-overlay">
                <p class="carousel-title">${movie.title}</p>
                <span class="carousel-rating">★ ${movie.vote_average?.toFixed(1) || 'N/A'}</span>
            </div>
        `;
        
        card.onclick = () => this.viewMovie(movie.id);
        
        return card;
    },
    
    /**
     * Generate star rating HTML
     */
    generateStars(rating) {
        const fullStars = Math.floor(rating / 2);
        const halfStar = rating % 2 >= 1;
        let stars = '';
        
        for (let i = 0; i < fullStars; i++) {
            stars += '<span class="star full">★</span>';
        }
        if (halfStar) {
            stars += '<span class="star half">★</span>';
        }
        for (let i = fullStars + (halfStar ? 1 : 0); i < 5; i++) {
            stars += '<span class="star empty">☆</span>';
        }
        
        return stars;
    },
    
    /**
     * Navigate to movie details page
     */
    viewMovie(movieId) {
        window.location.href = `/movie/${movieId}`;
    },
    
    /**
     * Show a notification
     */
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existing = document.querySelector('.notification');
        if (existing) existing.remove();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    },
    
    /**
     * Show loading spinner
     */
    showLoading(container) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                    <div class="spinner-ring"></div>
                </div>
                <p class="loading-text">Se încarcă...</p>
            </div>
        `;
    },
    
    /**
     * Show error message
     */
    showError(container, message = 'A apărut o eroare.') {
        container.innerHTML = `<p class="error-message">❌ ${message}</p>`;
    },
    
    /**
     * Show empty state
     */
    showEmpty(container, message = 'Nu s-au găsit rezultate.') {
        container.innerHTML = `<p class="no-results">${message}</p>`;
    }
};

/**
 * Utility Functions
 */
const Utils = {
    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Format number with locale
     */
    formatNumber(num) {
        return num?.toLocaleString() || '0';
    },
    
    /**
     * Extract year from date string
     */
    extractYear(dateString) {
        if (!dateString) return 'N/A';
        return dateString.split('-')[0];
    },
    
    /**
     * Truncate text
     */
    truncate(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
};

// Export for use in templates
window.API = API;
window.UI = UI;
window.Utils = Utils;
window.AppState = AppState;

