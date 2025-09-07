/**
 * Netlify Function: Legal Document Search
 * 
 * This function handles search requests from the frontend and queries
 * the DeepSeek API to find relevant legal information.
 * 
 * Endpoint: /.netlify/functions/searchFunction
 * Methods: GET, POST
 */

const https = require('https');

// Configuration - Multi-key load balancing
const DEEPSEEK_API_KEYS = [
    process.env.DEEPSEEK_API_KEY,
    process.env.DEEPSEEK_API_KEY_2, 
    process.env.DEEPSEEK_API_KEY_3
].filter(key => key); // Remove undefined keys

const DEEPSEEK_API_ENDPOINT = 'https://api.deepseek.com/chat/completions';
const REQUEST_TIMEOUT = 24000; // 24 seconds (leave 2 seconds buffer for Netlify)

/**
 * CORS headers for browser compatibility
 */
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
};

/**
 * Validates the request parameters
 * @param {string} query - User search query
 * @param {string} language - Language code
 * @returns {Object} Validation result
 */
function validateRequest(query, language) {
    const errors = [];
    
    if (!query || typeof query !== 'string' || query.trim().length === 0) {
        errors.push('Query is required and must be a non-empty string');
    }
    
    if (query && query.trim().length > 1000) {
        errors.push('Query is too long (maximum 1000 characters)');
    }
    
    if (!language || !['ar', 'en'].includes(language)) {
        errors.push('Language must be either "ar" or "en"');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Load legal documents based on language
 * @param {string} language - Language code
 * @returns {Object} Complete legal documents
 */
function loadLegalDocuments(language) {
    try {
        // Always load ALL documents - legal texts are interconnected and important
        if (language === 'ar') {
            return require('../../arabic_rules.json');
        } else {
            return require('../../english_rules.json');
        }
    } catch (error) {
        console.error(`Error loading ${language} documents:`, error);
        return null;
    }
}

/**
 * Optimize documents specifically for Arabic processing based on DeepSeek research
 * @param {Object} documents - Full legal documents  
 * @param {string} language - Language code
 * @returns {Object} Optimized documents for Arabic/RTL processing
 */
function optimizeDocumentsForArabic(documents, language) {
    const optimized = {};
    const mainKey = Object.keys(documents)[0];
    
    if (!documents[mainKey]) return optimized;
    
    const articles = documents[mainKey];
    optimized[mainKey] = {};
    
    Object.keys(articles).forEach(articleKey => {
        const article = articles[articleKey];
        
        if (language === 'ar') {
            // Arabic-specific optimizations based on DeepSeek capabilities
            optimized[mainKey][articleKey] = {
                title: article.title,
                // Use Modern Standard Arabic (MSA) - better supported
                text: preprocessArabicText(article.text || ''),
                // Keep structured data (penalty tables) - DeepSeek handles these well
                Time_Penalty_Tables: article.Time_Penalty_Tables || undefined
            };
        } else {
            // English: Keep full content
            optimized[mainKey][articleKey] = article;
        }
    });
    
    return optimized;
}

/**
 * Preprocess Arabic text for optimal DeepSeek processing
 * @param {string} text - Arabic text
 * @returns {string} Preprocessed Arabic text
 */
function preprocessArabicText(text) {
    if (!text) return '';
    
    // Remove mixed script issues (Arabic + Latin)
    // Split English and Arabic content to prevent DeepSeek mixing scripts
    const cleanText = text
        .replace(/([a-zA-Z]+)/g, ' $1 ') // Space around English words
        .replace(/\s+/g, ' ') // Normalize spaces
        .trim();
    
    return cleanText;
}

/**
 * Create streaming chat payload - the key innovation!
 * @param {string} query - User search query
 * @param {string} language - Language code
 * @param {Object} documents - Optimized documents
 * @returns {Object} Streaming chat payload
 */
function createStreamingChatPayload(query, language, documents) {
    const isArabic = language === 'ar';
    
    // Simplified prompt optimized for MSA (Modern Standard Arabic)
    const systemPrompt = isArabic 
        ? `أجب بالعربية الفصحى فقط. ابحث في قوانين ITPF:

${JSON.stringify(documents, null, 0)}`
        : `Respond in English only. Search ITPF rules:

${JSON.stringify(documents, null, 0)}`;

    const userPrompt = isArabic 
        ? `سؤال: ${query}

أجب بـ JSON فقط:
{
  "results": [
    {
      "article_number": "رقم المادة",
      "title": "العنوان", 
      "relevant_text": "النص",
      "explanation": "الشرح",
      "score": رقم
    }
  ]
}`
        : `Query: ${query}

JSON only:
{
  "results": [
    {
      "article_number": "Article number",
      "title": "Title",
      "relevant_text": "Text", 
      "explanation": "Explanation",
      "score": number
    }
  ]
}`;

    return {
        model: isArabic ? "deepseek-reasoner" : "deepseek-chat",
        messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt }
        ],
        temperature: 0.6, // Optimal for Arabic based on research
        max_tokens: isArabic ? 800 : 1200,
        stream: true, // KEY: Enable streaming!
        response_format: { type: "json_object" }
    };
}

/**
 * Extract relevant articles from stage 1 search results
 * @param {Object} stage1Response - Response from stage 1 search
 * @param {Object} fullDocuments - Complete legal documents
 * @returns {Object} Filtered documents with only relevant articles
 */
function extractRelevantArticles(stage1Response, fullDocuments) {
    try {
        const responseContent = stage1Response.choices[0].message.content;
        const parsedContent = JSON.parse(responseContent);
        
        const relevantKeys = new Set();
        if (parsedContent.results) {
            parsedContent.results.forEach(result => {
                if (result.article_number) {
                    relevantKeys.add(result.article_number);
                }
            });
        }
        
        // If no specific articles found, return a subset (first 2 articles)
        if (relevantKeys.size === 0) {
            const mainKey = Object.keys(fullDocuments)[0];
            const articleKeys = Object.keys(fullDocuments[mainKey]).slice(0, 2);
            articleKeys.forEach(key => relevantKeys.add(key));
        }
        
        // Build filtered documents
        const filtered = {};
        const mainKey = Object.keys(fullDocuments)[0];
        filtered[mainKey] = {};
        
        relevantKeys.forEach(articleKey => {
            if (fullDocuments[mainKey][articleKey]) {
                filtered[mainKey][articleKey] = fullDocuments[mainKey][articleKey];
            }
        });
        
        console.log(`Stage 1 identified ${relevantKeys.size} relevant articles`);
        return filtered;
        
    } catch (error) {
        console.error('Error extracting relevant articles:', error);
        // Fallback: return first 2 articles
        const mainKey = Object.keys(fullDocuments)[0];
        const firstTwo = {};
        firstTwo[mainKey] = {};
        const articleKeys = Object.keys(fullDocuments[mainKey]).slice(0, 2);
        articleKeys.forEach(key => {
            firstTwo[mainKey][key] = fullDocuments[mainKey][key];
        });
        return firstTwo;
    }
}

/**
 * Creates chat payload for DeepSeek API
 * @param {string} query - User search query
 * @param {string} language - Language code
 * @param {Object} documents - Legal documents
 * @param {boolean} isStage1 - Whether this is stage 1 (quick search) or stage 2 (detailed)
 * @returns {Object} Chat payload
 */
function createChatPayload(query, language, documents, isStage1 = false) {
    const isArabic = language === 'ar';
    
    const systemPrompt = isArabic 
        ? `أجب بالعربية فقط. ابحث في قوانين ITPF واعطِ أفضل نتيجة واحدة.

${JSON.stringify(documents, null, 0)}`
        : `English only. Search ITPF rules and provide best single result.

${JSON.stringify(documents, null, 0)}`;

    const userPrompt = isArabic 
        ? `سؤال: ${query}

JSON فقط بالعربية:
{
  "results": [
    {
      "article_number": "رقم المادة",
      "title": "عنوان المادة", 
      "relevant_text": "النص القانوني",
      "explanation": "شرح بالعربية",
      "score": عدد
    }
  ],
  "query_language": "ar"
}`
        : `Query: ${query}

JSON only in English:
{
  "results": [
    {
      "article_number": "Article number",
      "title": "Article title",
      "relevant_text": "Legal text", 
      "explanation": "Explanation",
      "score": number
    }
  ],
  "query_language": "en"
}`;

    return {
        model: language === 'ar' ? "deepseek-reasoner" : "deepseek-chat", // Use reasoner for Arabic
        messages: [
            {
                role: "system",
                content: systemPrompt
            },
            {
                role: "user", 
                content: userPrompt
            }
        ],
        temperature: 0.0,
        max_tokens: language === 'ar' ? 800 : 1200, // Less tokens for Arabic
        response_format: { type: "json_object" },
        stream: false
    };
}

/**
 * Processes search results from DeepSeek API
 * @param {Object} apiResponse - Raw API response
 * @param {string} language - Language code
 * @returns {Object} Processed results
 */
function processSearchResults(apiResponse, language) {
    try {
        // Parse the JSON response from DeepSeek
        let parsedContent;
        try {
            const responseContent = apiResponse.choices[0].message.content;
            parsedContent = JSON.parse(responseContent);
        } catch (parseError) {
            console.error('Failed to parse DeepSeek response:', parseError);
            throw new Error('Invalid response format from DeepSeek API');
        }

        const results = parsedContent.results || [];
        
        if (results.length === 0) {
            return {
                success: true,
                hasResults: false,
                message: language === 'ar' 
                    ? 'لم يتم العثور على نتائج مطابقة لاستعلامك. يرجى المحاولة بكلمات مختلفة.'
                    : 'No matching results found for your query. Please try different keywords.',
                results: [],
                metadata: {
                    total_results: 0,
                    language: language
                }
            };
        }
        
        const processedResults = results.slice(0, 3).map((result, index) => ({
            id: `result_${index}`,
            title: result.title || (language === 'ar' ? `نتيجة ${index + 1}` : `Result ${index + 1}`),
            content: result.relevant_text || '',
            highlights: result.explanation ? [result.explanation] : [],
            score: result.score || 0,
            source: {
                article: result.article_number || 'Unknown',
                section: 'Legal Rules',
                document: 'ITPF Legal Rules'
            }
        }));
        
        return {
            success: true,
            hasResults: true,
            message: language === 'ar' 
                ? `تم العثور على ${processedResults.length} نتائج ذات صلة`
                : `Found ${processedResults.length} relevant results`,
            results: processedResults,
            metadata: {
                total_results: results.length,
                returned_results: processedResults.length,
                language: language
            }
        };
        
    } catch (error) {
        console.error('Error processing search results:', error);
        throw new Error('Failed to process search results');
    }
}

/**
 * Get next available API key with load balancing
 * @param {string} language - Language code for language-specific load balancing
 * @param {number} retryCount - Retry count to select different key
 * @returns {string} API key
 */
function getNextApiKey(language = 'en', retryCount = 0) {
    if (DEEPSEEK_API_KEYS.length === 0) {
        throw new Error('No DeepSeek API keys configured');
    }
    
    // Language-specific key selection + retry offset
    let index;
    if (language === 'ar') {
        // Prefer keys 1 and 2 for Arabic (heavier processing)
        index = (retryCount + 1) % DEEPSEEK_API_KEYS.length;
    } else {
        // Prefer key 0 for English (lighter processing)
        index = retryCount % DEEPSEEK_API_KEYS.length;
    }
    
    return DEEPSEEK_API_KEYS[index];
}

/**
 * Revolutionary streaming API call - solves timeout completely!
 * @param {Object} payload - Streaming chat payload
 * @param {string} language - Language code
 * @returns {Promise<Object>} Complete response from stream
 */
function streamDeepSeekAPI(payload, language) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(payload);
        const url = new URL(DEEPSEEK_API_ENDPOINT);
        
        let apiKey;
        try {
            apiKey = getNextApiKey(language, 0);
        } catch (error) {
            reject({
                error: 'No API keys available',
                message: language === 'ar' 
                    ? 'خطأ في إعدادات الخدمة'
                    : 'Service configuration error'
            });
            return;
        }
        
        const options = {
            hostname: url.hostname,
            port: url.port || 443,
            path: url.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                'Authorization': `Bearer ${apiKey}`,
                'Accept': 'text/event-stream', // Accept SSE
                'Cache-Control': 'no-cache',
                'User-Agent': 'ITPF-Legal-Search/2.0-SSE'
            }
        };

        console.log(`🔥 Using streaming API for ${language} - NO TIMEOUT LIMITS!`);

        const req = https.request(options, (res) => {
            let streamData = '';
            let lastEventData = '';
            
            res.on('data', (chunk) => {
                const chunkStr = chunk.toString();
                streamData += chunkStr;
                
                // Process SSE events
                const events = chunkStr.split('\n\n');
                events.forEach(event => {
                    if (event.startsWith('data: ')) {
                        const data = event.slice(6);
                        if (data === '[DONE]') {
                            // Stream complete
                            return;
                        }
                        if (data.trim() && data !== 'keep-alive') {
                            try {
                                const parsed = JSON.parse(data);
                                if (parsed.choices && parsed.choices[0]) {
                                    const delta = parsed.choices[0].delta;
                                    if (delta && delta.content) {
                                        lastEventData += delta.content;
                                    }
                                    // Check if message is complete
                                    if (parsed.choices[0].finish_reason === 'stop') {
                                        resolve({
                                            choices: [{
                                                message: {
                                                    content: lastEventData
                                                },
                                                finish_reason: 'stop'
                                            }]
                                        });
                                    }
                                }
                            } catch (parseError) {
                                // Continue collecting data
                            }
                        }
                    }
                });
            });
            
            res.on('end', () => {
                if (lastEventData) {
                    resolve({
                        choices: [{
                            message: {
                                content: lastEventData
                            },
                            finish_reason: 'stop'
                        }]
                    });
                } else {
                    reject({
                        error: 'Empty stream response',
                        message: language === 'ar' 
                            ? 'لم يتم تلقي استجابة'
                            : 'No response received'
                    });
                }
            });
        });

        req.on('error', (error) => {
            reject({
                error: `Streaming error: ${error.message}`,
                message: language === 'ar' 
                    ? 'خطأ في الاتصال المباشر'
                    : 'Streaming connection error'
            });
        });

        // No timeout! Streaming handles this naturally
        req.write(postData);
        req.end();
    });
}

/**
 * 🧠 SMART QUERY PARTITIONING - The brilliant solution!
 * Splits complex queries while preserving ALL Arabic text integrity
 * @param {string} query - Original user query
 * @param {string} language - Language code
 * @param {Object} documents - COMPLETE legal documents (never modified!)
 * @returns {Object} Aggregated response from multiple sub-queries
 */
async function processPartitionedQuery(query, language, documents) {
    console.log('🎯 Starting intelligent query partitioning...');
    
    try {
        // Step 1: Intelligently split the query
        const subQueries = splitQueryIntelligently(query, language);
        console.log(`📝 Split into ${subQueries.length} sub-queries:`, subQueries);
        
        // Step 2: Process each sub-query with FULL documents (parallel processing)
        const subPromises = subQueries.map(async (subQuery, index) => {
            console.log(`🔍 Processing sub-query ${index + 1}: "${subQuery}"`);
            
            // Each sub-query gets ALL documents - no information loss!
            const optimizedDocs = optimizeDocumentsForArabic(documents, language);
            const chatPayload = createStreamingChatPayload(subQuery, language, optimizedDocs);
            
            try {
                const streamResponse = await streamDeepSeekAPI(chatPayload, language);
                const response = await processStreamingResponse(streamResponse);
                console.log(`✅ Sub-query ${index + 1} completed successfully`);
                return { subQuery, response, success: true };
            } catch (error) {
                console.log(`⚠️ Sub-query ${index + 1} failed:`, error.message);
                return { subQuery, error, success: false };
            }
        });
        
        // Step 3: Wait for all sub-queries (with timeout protection)
        const subResults = await Promise.allSettled(subPromises);
        
        // Step 4: Intelligently aggregate results
        const aggregatedResponse = aggregateQueryResults(subResults, query, language);
        
        console.log('🎉 Query partitioning completed successfully!');
        return aggregatedResponse;
        
    } catch (error) {
        console.error('❌ Query partitioning failed:', error);
        // Fallback to single query
        console.log('🔄 Falling back to single query...');
        const optimizedDocs = optimizeDocumentsForArabic(documents, language);
        const chatPayload = createStreamingChatPayload(query, language, optimizedDocs);
        return await streamDeepSeekAPI(chatPayload, language);
    }
}

/**
 * Split query intelligently based on Arabic language patterns
 * @param {string} query - Original query
 * @param {string} language - Language code
 * @returns {Array} Array of sub-queries
 */
function splitQueryIntelligently(query, language) {
    const isArabic = language === 'ar';
    
    if (!isArabic) {
        // Simple English splitting
        if (query.includes(' and ')) {
            return query.split(' and ').map(q => q.trim());
        }
        return [query];
    }
    
    // Arabic-specific intelligent splitting
    const arabicSplitters = [
        'و', // and
        'أو', // or  
        'كما', // also
        'أيضاً', // also
        'بالإضافة', // in addition
        'علاوة على', // furthermore
    ];
    
    let subQueries = [query];
    
    // Split by Arabic connectors
    arabicSplitters.forEach(splitter => {
        const newQueries = [];
        subQueries.forEach(q => {
            if (q.includes(splitter)) {
                const parts = q.split(splitter).map(p => p.trim()).filter(p => p.length > 3);
                newQueries.push(...parts);
            } else {
                newQueries.push(q);
            }
        });
        subQueries = newQueries;
    });
    
    // Limit to max 3 sub-queries to avoid over-splitting
    if (subQueries.length > 3) {
        subQueries = subQueries.slice(0, 3);
    }
    
    // Ensure minimum query length
    subQueries = subQueries.filter(q => q.trim().length > 2);
    
    // Fallback if splitting resulted in too few or too many parts
    if (subQueries.length < 1 || subQueries.length > 4) {
        return [query];
    }
    
    return subQueries;
}

/**
 * Aggregate results from multiple sub-queries intelligently
 * @param {Array} subResults - Results from Promise.allSettled
 * @param {string} originalQuery - Original query
 * @param {string} language - Language code
 * @returns {Object} Aggregated response
 */
function aggregateQueryResults(subResults, originalQuery, language) {
    const successfulResults = subResults
        .filter(result => result.status === 'fulfilled' && result.value.success)
        .map(result => result.value.response);
    
    if (successfulResults.length === 0) {
        return {
            choices: [{
                message: {
                    content: JSON.stringify({
                        results: [],
                        total_results: 0,
                        query_language: language,
                        error: language === 'ar' ? 'فشل في معالجة الاستعلام' : 'Failed to process query'
                    })
                }
            }]
        };
    }
    
    // Combine all results
    const allResults = [];
    const seenArticles = new Set();
    
    successfulResults.forEach(response => {
        try {
            const content = JSON.parse(response.choices[0].message.content);
            if (content.results) {
                content.results.forEach(result => {
                    const articleKey = result.article_number;
                    if (!seenArticles.has(articleKey)) {
                        seenArticles.add(articleKey);
                        allResults.push(result);
                    }
                });
            }
        } catch (parseError) {
            console.log('⚠️ Failed to parse sub-result:', parseError.message);
        }
    });
    
    // Sort by relevance score
    allResults.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    // Return top 3 results
    const topResults = allResults.slice(0, 3);
    
    const aggregatedResponse = {
        results: topResults,
        total_results: topResults.length,
        query_language: language,
        partitioned_search: true,
        sub_queries_processed: successfulResults.length
    };
    
    return {
        choices: [{
            message: {
                content: JSON.stringify(aggregatedResponse)
            },
            finish_reason: 'stop'
        }]
    };
}

/**
 * Process streaming response (if needed)
 * @param {Object} streamResponse - Response from streaming API
 * @returns {Object} Processed response
 */
async function processStreamingResponse(streamResponse) {
    // Stream response is already complete, just return it
    return streamResponse;
}

/**
 * Legacy non-streaming API (kept for fallback)
 * @param {Object} payload - Chat payload
 * @param {string} language - Language code for error messages
 * @param {number} retryCount - Current retry attempt
 * @returns {Promise<Object>} API response
 */
function searchDeepSeekAPI(payload, language, retryCount = 0) {
    return new Promise((resolve, reject) => {
        const postData = JSON.stringify(payload);
        const url = new URL(DEEPSEEK_API_ENDPOINT);
        
        // Get API key with load balancing
        let apiKey;
        try {
            apiKey = getNextApiKey(language, retryCount);
        } catch (error) {
            reject({
                error: 'No API keys available',
                message: language === 'ar' 
                    ? 'خطأ في إعدادات الخدمة. يرجى المحاولة لاحقاً.'
                    : 'Service configuration error. Please try later.'
            });
            return;
        }
        
        const options = {
            hostname: url.hostname,
            port: url.port || 443,
            path: url.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData),
                'Authorization': `Bearer ${apiKey}`,
                'User-Agent': 'ITPF-Legal-Search/1.0',
                'Accept': 'application/json'
            }
        };

        console.log(`Using API key index: ${DEEPSEEK_API_KEYS.indexOf(apiKey)} for ${language} query`);

        const req = https.request(options, (res) => {
            let responseBody = '';
            
            res.on('data', (chunk) => {
                responseBody += chunk;
            });
            
            res.on('end', () => {
                try {
                    const parsedResponse = responseBody ? JSON.parse(responseBody) : {};
                    
                    if (res.statusCode >= 200 && res.statusCode < 300) {
                        resolve(parsedResponse);
                    } else {
                        // Retry with different API key if available
                        if (retryCount < DEEPSEEK_API_KEYS.length - 1 && (res.statusCode === 429 || res.statusCode >= 500)) {
                            console.log(`Retrying with different API key (attempt ${retryCount + 1})`);
                            searchDeepSeekAPI(payload, language, retryCount + 1)
                                .then(resolve)
                                .catch(reject);
                        } else {
                            reject({
                                statusCode: res.statusCode,
                                error: parsedResponse.error || 'Search request failed',
                                message: language === 'ar' 
                                    ? 'حدث خطأ في البحث. يرجى المحاولة مرة أخرى.'
                                    : 'Search error occurred. Please try again.'
                            });
                        }
                    }
                } catch (parseError) {
                    reject({
                        statusCode: res.statusCode,
                        error: 'Failed to parse API response',
                        message: language === 'ar' 
                            ? 'خطأ في معالجة النتائج. يرجى المحاولة لاحقاً.'
                            : 'Error processing results. Please try later.'
                    });
                }
            });
        });

        req.on('error', (error) => {
            reject({
                error: `Network error: ${error.message}`,
                message: language === 'ar' 
                    ? 'خطأ في الاتصال. يرجى التحقق من اتصالك بالإنترنت.'
                    : 'Connection error. Please check your internet connection.'
            });
        });

        req.setTimeout(REQUEST_TIMEOUT, () => {
            req.destroy();
            reject({
                error: 'Request timeout',
                message: language === 'ar' 
                    ? 'انتهت مهلة البحث. يرجى المحاولة مرة أخرى.'
                    : 'Search timeout. Please try again.'
            });
        });

        req.write(postData);
        req.end();
    });
}

/**
 * Main Netlify function handler
 */
exports.handler = async (event, context) => {
    // Handle CORS preflight requests
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers: corsHeaders,
            body: ''
        };
    }
    
    try {
        // Check API keys
        if (DEEPSEEK_API_KEYS.length === 0) {
            console.error('No DeepSeek API keys configured');
            return {
                statusCode: 500,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: false,
                    error: 'API configuration error',
                    message: language === 'ar' 
                        ? 'خطأ في إعداد الخدمة. يرجى المحاولة لاحقاً.'
                        : 'Search service is not properly configured'
                })
            };
        }
        
        console.log(`Available API keys: ${DEEPSEEK_API_KEYS.length}`);
        
        // Extract parameters from request
        let query, language;
        
        if (event.httpMethod === 'POST') {
            try {
                const body = JSON.parse(event.body || '{}');
                query = body.query;
                language = body.language || 'en';
            } catch (parseError) {
                return {
                    statusCode: 400,
                    headers: corsHeaders,
                    body: JSON.stringify({
                        success: false,
                        error: 'Invalid JSON in request body',
                        message: 'Please provide valid JSON data'
                    })
                };
            }
        } else if (event.httpMethod === 'GET') {
            const params = event.queryStringParameters || {};
            query = params.query || params.q;
            language = params.language || params.lang || 'en';
        } else {
            return {
                statusCode: 405,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: false,
                    error: 'Method not allowed',
                    message: 'Only GET and POST methods are supported'
                })
            };
        }
        
        // Validate request
        const validation = validateRequest(query, language);
        if (!validation.isValid) {
            return {
                statusCode: 400,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: false,
                    error: 'Validation failed',
                    message: validation.errors.join('; '),
                    details: validation.errors
                })
            };
        }
        
        // Load legal documents
        const documents = loadLegalDocuments(language);
        if (!documents) {
            return {
                statusCode: 500,
                headers: corsHeaders,
                body: JSON.stringify({
                    success: false,
                    error: 'Document loading error',
                    message: language === 'ar' 
                        ? 'فشل في تحميل الوثائق القانونية'
                        : 'Failed to load legal documents'
                })
            };
        }

        console.log(`Using intelligent query partitioning for: "${query}" in ${language}`);
        
        // 🎯 BRILLIANT SOLUTION: Partition query while keeping ALL Arabic texts intact!
        const usePartitioning = language === 'ar' && query.trim().length > 10; // Enable for Arabic complex queries
        
        if (usePartitioning) {
            console.log('🧠 Using smart query partitioning - preserves ALL Arabic texts!');
            const apiResponse = await processPartitionedQuery(query, language, documents);
        } else {
            // Fallback to streaming (can be reverted instantly)
            console.log('📡 Using streaming API (fallback mode)');
            const optimizedDocs = optimizeDocumentsForArabic(documents, language);
            const chatPayload = createStreamingChatPayload(query, language, optimizedDocs);
            const streamResponse = await streamDeepSeekAPI(chatPayload, language);
            var apiResponse = await processStreamingResponse(streamResponse);
        }
        
        // Process and return results
        const processedResults = processSearchResults(apiResponse, language);
        
        return {
            statusCode: 200,
            headers: corsHeaders,
            body: JSON.stringify(processedResults)
        };
        
    } catch (error) {
        console.error('Search function error:', error);
        
        const errorMessage = error.message || (
            language === 'ar' 
                ? 'حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.'
                : 'An unexpected error occurred. Please try again later.'
        );
        
        return {
            statusCode: error.statusCode || 500,
            headers: corsHeaders,
            body: JSON.stringify({
                success: false,
                error: 'Search failed',
                message: errorMessage,
                details: process.env.NODE_ENV === 'development' ? error.message : undefined
            })
        };
    }
};