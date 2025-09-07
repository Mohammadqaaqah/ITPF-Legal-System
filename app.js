/**
 * ITPF Legal Query System - Frontend JavaScript
 * 
 * Features:
 * - Bilingual language switching (Arabic/English)
 * - Search functionality with Netlify Functions
 * - Dynamic UI updates
 * - Error handling and loading states
 * - Accessibility support
 */

class ITTPFLegalSearch {
    constructor() {
        this.currentLanguage = 'en';
        this.isSearching = false;
        this.searchCache = new Map();
        
        // DOM Elements
        this.elements = {
            languageToggle: document.getElementById('languageToggle'),
            searchForm: document.getElementById('searchForm'),
            searchQuery: document.getElementById('searchQuery'),
            searchButton: document.getElementById('searchButton'),
            charCount: document.getElementById('charCount'),
            
            // Results elements
            resultsSection: document.getElementById('resultsSection'),
            loadingState: document.getElementById('loadingState'),
            resultsContainer: document.getElementById('resultsContainer'),
            errorState: document.getElementById('errorState'),
            noResultsState: document.getElementById('noResultsState'),
            errorMessage: document.getElementById('errorMessage'),
            retryButton: document.getElementById('retryButton')
        };
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    init() {
        this.setupEventListeners();
        this.updateLanguageDisplay();
        this.loadFromCache();
        console.log('🚀 ITPF Legal Search initialized');
    }
    
    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Language toggle
        this.elements.languageToggle.addEventListener('click', (e) => {
            if (e.target.dataset.lang) {
                this.switchLanguage(e.target.dataset.lang);
            }
        });
        
        // Search form
        this.elements.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSearch();
        });
        
        // Character counter
        this.elements.searchQuery.addEventListener('input', () => {
            this.updateCharacterCounter();
        });
        
        // Retry button
        this.elements.retryButton.addEventListener('click', () => {
            this.handleSearch();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.elements.searchQuery.focus();
            }
            
            // Alt + L to toggle language
            if (e.altKey && e.key === 'l') {
                e.preventDefault();
                const newLang = this.currentLanguage === 'en' ? 'ar' : 'en';
                this.switchLanguage(newLang);
            }
        });
        
        // Auto-resize textarea
        this.elements.searchQuery.addEventListener('input', this.autoResizeTextarea.bind(this));
    }
    
    /**
     * Switch language between English and Arabic
     * @param {string} language - Language code ('en' or 'ar')
     */
    switchLanguage(language) {
        if (language === this.currentLanguage) return;
        
        this.currentLanguage = language;
        
        // Update document attributes
        document.documentElement.lang = language;
        document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
        document.body.dataset.lang = language;
        
        // Update toggle buttons
        this.elements.languageToggle.querySelectorAll('.toggle-option').forEach(option => {
            option.classList.toggle('active', option.dataset.lang === language);
        });
        
        // Update placeholder
        this.updateSearchPlaceholder();
        
        // Save preference
        localStorage.setItem('itpf-language', language);
        
        console.log(`🌐 Language switched to: ${language}`);
    }
    
    /**
     * Update language-specific UI elements
     */
    updateLanguageDisplay() {
        const savedLanguage = localStorage.getItem('itpf-language') || 'en';
        this.switchLanguage(savedLanguage);
    }
    
    /**
     * Update search input placeholder based on current language
     */
    updateSearchPlaceholder() {
        const placeholders = {
            en: 'Enter your legal question here...',
            ar: 'أدخل سؤالك القانوني هنا...'
        };
        
        this.elements.searchQuery.placeholder = placeholders[this.currentLanguage];
    }
    
    /**
     * Update character counter
     */
    updateCharacterCounter() {
        const length = this.elements.searchQuery.value.length;
        this.elements.charCount.textContent = length;
        
        // Add warning class if approaching limit
        this.elements.charCount.parentElement.classList.toggle('warning', length > 900);
    }
    
    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea() {
        const textarea = this.elements.searchQuery;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 300) + 'px';
    }
    
    /**
     * Handle search form submission
     */
    async handleSearch() {
        const query = this.elements.searchQuery.value.trim();
        
        // Validate input
        if (!query) {
            this.showError(
                this.currentLanguage === 'ar' 
                    ? 'يرجى إدخال سؤال قانوني للبحث'
                    : 'Please enter a legal question to search'
            );
            return;
        }
        
        if (query.length < 3) {
            this.showError(
                this.currentLanguage === 'ar'
                    ? 'يجب أن يحتوي السؤال على 3 أحرف على الأقل'
                    : 'Question must be at least 3 characters long'
            );
            return;
        }
        
        // Check cache first
        const cacheKey = `${query}-${this.currentLanguage}`;
        if (this.searchCache.has(cacheKey)) {
            console.log('📋 Using cached results');
            this.displayResults(this.searchCache.get(cacheKey));
            return;
        }
        
        await this.performSearch(query);
    }
    
    /**
     * Perform search API call
     * @param {string} query - Search query
     */
    async performSearch(query) {
        this.setSearchingState(true);
        this.showLoadingState();
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    language: this.currentLanguage
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Search request failed');
            }
            
            if (!data.success) {
                throw new Error(data.message || 'Search was not successful');
            }
            
            // Cache successful results
            const cacheKey = `${query}-${this.currentLanguage}`;
            this.searchCache.set(cacheKey, data);
            
            // Limit cache size
            if (this.searchCache.size > 50) {
                const firstKey = this.searchCache.keys().next().value;
                this.searchCache.delete(firstKey);
            }
            
            this.displayResults(data);
            
        } catch (error) {
            console.error('🔴 Search error:', error);
            this.showError(error.message);
        } finally {
            this.setSearchingState(false);
        }
    }
    
    /**
     * Set searching state UI
     * @param {boolean} isSearching - Whether currently searching
     */
    setSearchingState(isSearching) {
        this.isSearching = isSearching;
        
        this.elements.searchButton.disabled = isSearching;
        this.elements.searchButton.classList.toggle('loading', isSearching);
        
        if (isSearching) {
            this.elements.searchButton.setAttribute('aria-label', 'Searching...');
        } else {
            this.elements.searchButton.removeAttribute('aria-label');
        }
    }
    
    /**
     * Show loading state
     */
    showLoadingState() {
        this.hideAllStates();
        this.elements.loadingState.classList.add('active');
        this.elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Display search results
     * @param {Object} data - Search results data
     */
    displayResults(data) {
        this.hideAllStates();
        
        if (!data.hasResults || data.results.length === 0) {
            this.showNoResults(data.message);
            return;
        }
        
        this.renderResults(data);
        this.elements.resultsContainer.classList.add('active', 'fade-in');
        this.elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Render search results HTML
     * @param {Object} data - Search results data
     */
    renderResults(data) {
        const resultsHTML = `
            <div class="results-header slide-up">
                <div class="results-count">${data.message}</div>
                <div class="results-meta">
                    ${this.currentLanguage === 'ar' 
                        ? `وقت البحث: ${data.metadata.search_time || 0}ms`
                        : `Search time: ${data.metadata.search_time || 0}ms`
                    }
                </div>
            </div>
            
            <div class="results-list">
                ${data.results.map((result, index) => this.renderResultItem(result, index)).join('')}
            </div>
        `;
        
        this.elements.resultsContainer.innerHTML = resultsHTML;
    }
    
    /**
     * Render individual result item
     * @param {Object} result - Single result object
     * @param {number} index - Result index
     * @returns {string} HTML string
     */
    renderResultItem(result, index) {
        const animationDelay = `style="animation-delay: ${index * 0.1}s"`;
        
        return `
            <div class="result-item slide-up" ${animationDelay}>
                <div class="result-header">
                    <h3 class="result-title">${this.escapeHtml(result.title)}</h3>
                    <div class="result-score">${result.score}%</div>
                </div>
                
                <div class="result-content">
                    ${this.formatResultContent(result.content, result.highlights)}
                </div>
                
                <div class="result-source">
                    <div class="source-item">
                        <span class="source-label">
                            ${this.currentLanguage === 'ar' ? 'المادة:' : 'Article:'}
                        </span>
                        <span>${this.escapeHtml(result.source.article)}</span>
                    </div>
                    
                    <div class="source-item">
                        <span class="source-label">
                            ${this.currentLanguage === 'ar' ? 'القسم:' : 'Section:'}
                        </span>
                        <span>${this.escapeHtml(result.source.section)}</span>
                    </div>
                    
                    <div class="source-item">
                        <span class="source-label">
                            ${this.currentLanguage === 'ar' ? 'المصدر:' : 'Source:'}
                        </span>
                        <span>${this.escapeHtml(result.source.document)}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Format result content with highlights
     * @param {string} content - Original content
     * @param {Array} highlights - Highlight terms
     * @returns {string} Formatted content
     */
    formatResultContent(content, highlights = []) {
        let formattedContent = this.escapeHtml(content);
        
        // Apply highlights
        highlights.forEach(highlight => {
            const regex = new RegExp(`(${this.escapeRegex(highlight)})`, 'gi');
            formattedContent = formattedContent.replace(regex, '<span class="result-highlight">$1</span>');
        });
        
        // Convert paragraphs
        const paragraphs = formattedContent.split('\n\n');
        return paragraphs.map(p => p.trim() ? `<p>${p}</p>` : '').join('');
    }
    
    /**
     * Show no results state
     * @param {string} message - No results message
     */
    showNoResults(message) {
        this.hideAllStates();
        
        // Update the no results message if provided
        if (message) {
            const messageElement = this.elements.noResultsState.querySelector('.no-results-title');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
        
        this.elements.noResultsState.classList.add('active', 'fade-in');
        this.elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Show error state
     * @param {string} message - Error message
     */
    showError(message) {
        this.hideAllStates();
        this.elements.errorMessage.textContent = message;
        this.elements.errorState.classList.add('active', 'fade-in');
        this.elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    /**
     * Hide all result states
     */
    hideAllStates() {
        [
            this.elements.loadingState,
            this.elements.resultsContainer,
            this.elements.errorState,
            this.elements.noResultsState
        ].forEach(element => {
            element.classList.remove('active', 'fade-in', 'slide-up');
        });
    }
    
    /**
     * Load cached data on page load
     */
    loadFromCache() {
        // Clear old cache entries (older than 1 hour)
        const oneHour = 60 * 60 * 1000;
        const now = Date.now();
        
        for (const [key, value] of this.searchCache.entries()) {
            if (value.timestamp && (now - value.timestamp) > oneHour) {
                this.searchCache.delete(key);
            }
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Escape regex special characters
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\\]\\]/g, '\\\\$&');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        window.itpfSearch = new ITTPFLegalSearch();
    } catch (error) {
        console.error('🔴 Failed to initialize ITPF Legal Search:', error);
        
        // Show fallback error message
        const errorHTML = `
            <div style="text-align: center; padding: 2rem; color: #dc2626;">
                <h3>Application Error</h3>
                <p>Failed to initialize the search system. Please refresh the page and try again.</p>
            </div>
        `;
        
        const main = document.querySelector('.main');
        if (main) {
            main.innerHTML = errorHTML;
        }
    }
});

// Service Worker registration (optional, for offline support)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            // Register service worker if available
            // await navigator.serviceWorker.register('/sw.js');
            // console.log('🔧 Service Worker registered');
        } catch (error) {
            console.log('🔧 Service Worker registration skipped');
        }
    });
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ITTPFLegalSearch;
}