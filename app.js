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
        this.currentMode = 'search';  // 'search' or 'answer'
        this.isSearching = false;
        this.cacheVersion = '12.1'; // Phase 3: Complete Appendices Integration + Enhanced Search
        this.searchCache = new Map();
        this.answerCache = new Map();
        
        // DOM Elements
        this.elements = {
            languageToggle: document.getElementById('languageToggle'),
            searchForm: document.getElementById('searchForm'),
            searchQuery: document.getElementById('searchQuery'),
            searchButton: document.getElementById('searchButton'),
            charCount: document.getElementById('charCount'),
            
            // Mode toggle elements
            searchMode: document.getElementById('searchMode'),
            answerMode: document.getElementById('answerMode'),
            searchLabel: document.getElementById('searchLabel'),
            submitIcon: document.getElementById('submitIcon'),
            submitText: document.getElementById('submitText'),
            loadingText: document.getElementById('loadingText'),
            
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
        
        // Mode toggle
        this.elements.searchMode.addEventListener('click', () => {
            this.switchMode('search');
        });
        
        this.elements.answerMode.addEventListener('click', () => {
            this.switchMode('answer');
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
        
        // Update placeholders and submit button
        this.updatePlaceholders();
        this.updateSubmitButton();
        
        // Save preference
        localStorage.setItem('itpf-language', language);
        
        console.log(`🌐 Language switched to: ${language}`);
    }
    
    /**
     * Update language-specific UI elements
     */
    updateLanguageDisplay() {
        const savedLanguage = localStorage.getItem('itpf-language') || 'en';
        const savedMode = localStorage.getItem('itpf-mode') || 'search';
        this.switchLanguage(savedLanguage);
        this.switchMode(savedMode);
    }
    
    /**
     * Switch between search and answer modes
     * @param {string} mode - Mode ('search' or 'answer')
     */
    switchMode(mode) {
        if (mode === this.currentMode) return;
        
        this.currentMode = mode;
        
        // Update mode buttons
        this.elements.searchMode.classList.toggle('active', mode === 'search');
        this.elements.answerMode.classList.toggle('active', mode === 'answer');
        
        // Update placeholders and UI elements
        this.updatePlaceholders();
        this.updateSubmitButton();
        
        // Save preference
        localStorage.setItem('itpf-mode', mode);
        
        console.log(`🔄 Mode switched to: ${mode}`);
    }
    
    /**
     * Update placeholders based on current mode and language
     */
    updatePlaceholders() {
        // Hide all placeholders first
        const placeholders = this.elements.searchLabel.querySelectorAll('span');
        placeholders.forEach(span => span.style.display = 'none');
        
        // Show appropriate placeholders
        if (this.currentMode === 'search') {
            const searchPlaceholders = this.elements.searchLabel.querySelectorAll('.search-placeholder');
            searchPlaceholders.forEach(span => {
                if (span.getAttribute('data-lang-text').includes(this.currentLanguage)) {
                    span.style.display = 'inline';
                }
            });
        } else {
            const questionPlaceholders = this.elements.searchLabel.querySelectorAll('.question-placeholder');
            questionPlaceholders.forEach(span => {
                if (span.getAttribute('data-lang-text').includes(this.currentLanguage)) {
                    span.style.display = 'inline';
                }
            });
        }
    }
    
    /**
     * Update submit button based on current mode
     */
    updateSubmitButton() {
        // Update icon
        this.elements.submitIcon.textContent = this.currentMode === 'search' ? '🔍' : '💬';
        
        // Hide all button texts first
        const buttonTexts = this.elements.submitText.querySelectorAll('span');
        buttonTexts.forEach(span => span.style.display = 'none');
        
        // Show appropriate button text
        const textClass = this.currentMode === 'search' ? '.search-btn-text' : '.ask-btn-text';
        const targetTexts = this.elements.submitText.querySelectorAll(textClass);
        targetTexts.forEach(span => {
            if (span.getAttribute('data-lang-text').includes(this.currentLanguage)) {
                span.style.display = 'inline';
            }
        });
    }
    
    /**
     * Update search input placeholder based on current language
     */
    updateSearchPlaceholder() {
        this.updatePlaceholders();
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
        const cache = this.currentMode === 'search' ? this.searchCache : this.answerCache;
        const cacheKey = `${query}-${this.currentLanguage}-${this.currentMode}-${this.cacheVersion}`;
        if (cache.has(cacheKey)) {
            console.log('📋 Using cached results');
            if (this.currentMode === 'search') {
                this.displayResults(cache.get(cacheKey));
            } else {
                this.displayAnswer(cache.get(cacheKey));
            }
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
            const endpoint = this.currentMode === 'search' ? '/api/search' : '/api/answer';
            const apiUrl = `https://itpf-legal-search-c06wc8tdx-mohammadqaaqahs-projects.vercel.app${endpoint}`;
            
            const requestBody = this.currentMode === 'search' 
                ? { query: query, language: this.currentLanguage }
                : { question: query, language: this.currentLanguage };
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Search request failed');
            }
            
            if (!data.success) {
                throw new Error(data.message || 'Search was not successful');
            }
            
            // Cache successful results
            const cache = this.currentMode === 'search' ? this.searchCache : this.answerCache;
            const cacheKey = `${query}-${this.currentLanguage}-${this.currentMode}-${this.cacheVersion}`;
            cache.set(cacheKey, data);
            
            // Limit cache size
            if (cache.size > 50) {
                const firstKey = cache.keys().next().value;
                cache.delete(firstKey);
            }
            
            if (this.currentMode === 'search') {
                this.displayResults(data);
            } else {
                this.displayAnswer(data);
            }
            
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
        
        // Update loading text based on mode
        const loadingTexts = this.elements.loadingText.querySelectorAll('span');
        loadingTexts.forEach(span => span.style.display = 'none');
        
        const loadingClass = this.currentMode === 'search' ? '.loading-search' : '.loading-answer';
        const targetTexts = this.elements.loadingText.querySelectorAll(loadingClass);
        targetTexts.forEach(span => {
            if (span.getAttribute('data-lang-text').includes(this.currentLanguage)) {
                span.style.display = 'inline';
            }
        });
        
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
     * Display Q&A answer
     * @param {Object} data - Answer data
     */
    displayAnswer(data) {
        this.hideAllStates();
        
        if (!data.success) {
            this.showError(data.message);
            return;
        }
        
        this.renderAnswer(data);
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
     * Render Q&A answer HTML
     * @param {Object} data - Answer data
     */
    renderAnswer(data) {
        const answerHTML = `
            <div class="answer-header slide-up">
                <h3 class="answer-title">
                    ${this.currentLanguage === 'ar' ? 'الإجابة:' : 'Answer:'}
                </h3>
                <div class="answer-meta">
                    ${this.currentLanguage === 'ar' 
                        ? `مستوى الثقة: ${data.metadata.answer_confidence || 'متوسط'}`
                        : `Confidence: ${data.metadata.answer_confidence || 'medium'}`
                    }
                </div>
            </div>
            
            <div class="answer-content slide-up">
                <div class="answer-text">
                    ${this.formatAnswerContent(data.answer)}
                </div>
            </div>
            
            ${data.supporting_articles && data.supporting_articles.length > 0 ? `
            <div class="supporting-articles slide-up">
                <h4 class="supporting-title">
                    ${this.currentLanguage === 'ar' ? 'المواد الداعمة:' : 'Supporting Articles:'}
                </h4>
                <div class="supporting-list">
                    ${data.supporting_articles.map((article, index) => this.renderSupportingArticle(article, index)).join('')}
                </div>
            </div>
            ` : ''}
        `;
        
        this.elements.resultsContainer.innerHTML = answerHTML;
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
     * Format answer content
     * @param {string} content - Answer content
     * @returns {string} Formatted content
     */
    formatAnswerContent(content) {
        let formattedContent = this.escapeHtml(content);
        
        // Handle related articles section
        if (formattedContent.includes('--- المواد القانونية ذات الصلة ---') || 
            formattedContent.includes('--- Related Legal Articles ---')) {
            
            const parts = formattedContent.split(/--- (?:المواد القانونية ذات الصلة|Related Legal Articles) ---/);
            const mainContent = parts[0];
            const relatedContent = parts[1];
            
            // Format main content
            let formattedMain = this.formatParagraphs(mainContent);
            
            // Format related articles if they exist
            if (relatedContent) {
                const sectionTitle = formattedContent.includes('--- المواد القانونية ذات الصلة ---') 
                    ? 'المواد القانونية ذات الصلة' 
                    : 'Related Legal Articles';
                
                formattedMain += `
                    <div class="related-articles-section">
                        <h4 class="related-articles-title">${sectionTitle}</h4>
                        <div class="related-articles-content">
                            ${this.formatRelatedArticles(relatedContent)}
                        </div>
                    </div>
                `;
            }
            
            return formattedMain;
        }
        
        // Format regular content
        return this.formatParagraphs(formattedContent);
    }
    
    /**
     * Format paragraphs from content
     * @param {string} content - Content to format
     * @returns {string} Formatted paragraphs
     */
    formatParagraphs(content) {
        const paragraphs = content.split('\n\n');
        return paragraphs.map(p => {
            const trimmed = p.trim();
            if (trimmed) {
                // Handle single line breaks within paragraphs
                const formatted = trimmed.replace(/\n/g, '<br>');
                return `<p>${formatted}</p>`;
            }
            return '';
        }).join('');
    }
    
    /**
     * Format related articles section
     * @param {string} content - Related articles content
     * @returns {string} Formatted related articles
     */
    formatRelatedArticles(content) {
        const articles = content.split(/\n(?=\d+\.)/);
        
        return articles.map(article => {
            const trimmed = article.trim();
            if (!trimmed) return '';
            
            // Split article number and title from content
            const lines = trimmed.split('\n');
            const titleLine = lines[0]; // "2. المادة 126: عنوان المادة"
            const articleContent = lines.slice(1).join('\n');
            
            if (titleLine && articleContent) {
                return `
                    <div class="related-article-item">
                        <h5 class="related-article-title">${titleLine}</h5>
                        <div class="related-article-text">
                            ${this.formatParagraphs(articleContent)}
                        </div>
                    </div>
                `;
            }
            
            return `<div class="related-article-item">${this.formatParagraphs(trimmed)}</div>`;
        }).join('');
    }
    
    /**
     * Render supporting article
     * @param {Object} article - Supporting article
     * @param {number} index - Article index
     * @returns {string} HTML string
     */
    renderSupportingArticle(article, index) {
        return `
            <div class="supporting-article">
                <div class="supporting-header">
                    <h5 class="supporting-article-title">${this.escapeHtml(article.title)}</h5>
                    <span class="supporting-score">${article.score}%</span>
                </div>
                <div class="supporting-content">
                    <div class="supporting-text">${this.escapeHtml(article.content)}</div>
                </div>
                <div class="supporting-source">
                    ${this.currentLanguage === 'ar' ? 'المصدر:' : 'Source:'} 
                    ${this.escapeHtml(article.source.article)}
                </div>
            </div>
        `;
    }
    
    /**
     * Load cached data on page load
     */
    loadFromCache() {
        // Clear old cache entries (older than 1 hour)
        const oneHour = 60 * 60 * 1000;
        const now = Date.now();
        
        // Clear search cache
        for (const [key, value] of this.searchCache.entries()) {
            if (value.timestamp && (now - value.timestamp) > oneHour) {
                this.searchCache.delete(key);
            }
        }
        
        // Clear answer cache
        for (const [key, value] of this.answerCache.entries()) {
            if (value.timestamp && (now - value.timestamp) > oneHour) {
                this.answerCache.delete(key);
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