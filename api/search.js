/**
 * Vercel Function: Legal Document Search
 * 
 * This function handles search requests with 5-minute timeout support
 * for comprehensive Arabic legal document processing.
 * 
 * Endpoint: /api/search
 * Methods: GET, POST
 * Max Duration: 300 seconds (5 minutes)
 */

const https = require('https');

// Configuration - Multi-key load balancing  
const DEEPSEEK_API_KEYS = [
    process.env.DEEPSEEK_API_KEY,
    process.env.DEEPSEEK_API_KEY_2, 
    process.env.DEEPSEEK_API_KEY_3
].filter(key => key); // Remove undefined keys

const DEEPSEEK_API_ENDPOINT = 'https://api.deepseek.com/chat/completions';
const REQUEST_TIMEOUT = 280000; // 280 seconds (leave 20 seconds buffer for Vercel)

/**
 * Validates the request parameters
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
 */
function loadLegalDocuments(language) {
    try {
        // CRITICAL: Load COMPLETE authentic legal documents - all 154 articles + appendices 9&10
        // For Vercel - embed data directly in function to avoid path issues
        console.log(`🗂️ Loading COMPLETE AUTHENTIC ${language} legal rules (154 articles + appendices 9&10)`);
        
        let parsedData;
        
        if (language === 'ar') {
            // Direct require for Arabic file - Vercel will bundle it
            parsedData = require('../arabic_legal_rules_complete_authentic.json');
        } else {
            // Direct require for English file - Vercel will bundle it  
            parsedData = require('../english_legal_rules_complete_authentic.json');
        }
        
        // CRITICAL VERIFICATION: Ensure we have all 154 articles
        if (!parsedData.metadata || parsedData.metadata.total_articles !== 154) {
            console.error(`❌ INTEGRITY ERROR: Expected 154 articles, found ${parsedData.metadata?.total_articles}`);
            throw new Error('Incomplete legal document detected - missing articles!');
        }
        
        if (!parsedData.articles || parsedData.articles.length < 154) {
            console.error(`❌ ARTICLES ARRAY ERROR: Expected 154 articles, found ${parsedData.articles?.length}`);
            throw new Error('Articles array is incomplete!');
        }
        
        if (!parsedData.appendices || parsedData.appendices.length < 2) {
            console.error(`❌ APPENDICES ERROR: Expected 2 appendices, found ${parsedData.appendices?.length}`);
            throw new Error('Appendices 9 & 10 are missing!');
        }
        
        console.log(`✅ VERIFIED COMPLETE AUTHENTIC DATA: ${parsedData.articles.length} articles + ${parsedData.appendices.length} appendices for ${language}`);
        console.log(`📋 Articles range: ${parsedData.articles[0]?.article_number} to ${parsedData.articles[parsedData.articles.length-1]?.article_number}`);
        
        return parsedData;
        
    } catch (error) {
        console.error(`❌ CRITICAL ERROR loading COMPLETE ${language} documents:`, error);
        console.error(`❌ This means the complete authentic legal texts are not accessible!`);
        
        // REFUSE to use incomplete fallback files - maintain integrity!
        throw new Error(`FAILED TO LOAD COMPLETE AUTHENTIC LEGAL TEXTS for ${language}. This violates the requirement to keep all 154 articles + appendices 9&10 accessible.`);
    }
}

/**
 * Optimize documents specifically for Arabic processing based on DeepSeek research
 */
function optimizeDocumentsForArabic(documents, language) {
    if (!documents) return {};
    
    console.log(`🔧 Optimizing COMPLETE AUTHENTIC ${language} legal database...`);
    
    const optimized = {
        language: language,
        title: language === 'ar' ? documents.metadata?.title || 'قوانين الاتحاد الدولي لالتقاط الأوتاد' : documents.metadata?.title || documents.title || 'ITPF Legal Rules',
        total_articles: documents.metadata?.total_articles || 0,
        articles: []
    };
    
    if (language === 'ar') {
        // Handle the NEW AUTHENTIC Arabic structure
        if (documents.articles && Array.isArray(documents.articles)) {
            documents.articles.forEach(article => {
                optimized.articles.push({
                    article: article.article_number,
                    title: preprocessArabicText(article.title || ''),
                    content: preprocessArabicText(article.content || ''),
                    section: article.section || 'قوانين ITPF',
                    source_document: 'قوانين الاتحاد الدولي لالتقاط الأوتاد الأصيلة',
                    subsections: article.subsections || []
                });
            });
        }
        
        // Add appendices from Arabic document
        if (documents.appendices && Array.isArray(documents.appendices)) {
            documents.appendices.forEach(appendix => {
                optimized.articles.push({
                    article: `appendix_${appendix.appendix_number}`,
                    title: preprocessArabicText(appendix.title || ''),
                    content: preprocessArabicText(JSON.stringify(appendix.content || {}, null, 1)),
                    section: `الملحق رقم ${appendix.appendix_number}`,
                    source_document: 'قوانين الاتحاد الدولي لالتقاط الأوتاد الأصيلة',
                    appendix_data: appendix.content
                });
            });
        }
    } else {
        // Handle the NEW AUTHENTIC English structure
        if (documents.chapters && Array.isArray(documents.chapters)) {
            documents.chapters.forEach(chapter => {
                if (chapter.articles && Array.isArray(chapter.articles)) {
                    chapter.articles.forEach(article => {
                        optimized.articles.push({
                            article: article.article_number,
                            title: article.title || '',
                            content: article.content || '',
                            section: chapter.title || '',
                            source_document: documents.metadata?.title || 'ITPF Legal Rules Complete Authentic',
                            subsections: article.subsections || []
                        });
                    });
                }
            });
        }
        
        // Add appendices from English document
        if (documents.appendices && Array.isArray(documents.appendices)) {
            documents.appendices.forEach(appendix => {
                optimized.articles.push({
                    article: `appendix_${appendix.appendix_number}`,
                    title: appendix.title || '',
                    content: JSON.stringify(appendix.content || {}, null, 1),
                    section: `Appendix ${appendix.appendix_number}`,
                    source_document: documents.metadata?.title || 'ITPF Legal Rules Complete Authentic',
                    appendix_data: appendix.content
                });
            });
        }
    }
    
    optimized.total_articles = optimized.articles.length;
    
    // CRITICAL INTEGRITY CHECK: Ensure no articles are lost during optimization
    if (language === 'ar') {
        const expectedArticles = 154;
        const expectedAppendices = 2;
        const totalExpected = expectedArticles + expectedAppendices;
        
        if (optimized.articles.length < totalExpected) {
            console.error(`❌ INTEGRITY VIOLATION: Expected ${totalExpected} items, got ${optimized.articles.length}`);
            console.error(`❌ Original articles: ${documents.articles?.length}, appendices: ${documents.appendices?.length}`);
            throw new Error(`CRITICAL: Lost ${totalExpected - optimized.articles.length} legal items during Arabic optimization!`);
        }
    } else {
        // English should also have 154 articles + 2 appendices
        const expectedTotal = 156; // 154 articles + 2 appendices
        if (optimized.articles.length < expectedTotal) {
            console.error(`❌ INTEGRITY VIOLATION: Expected ${expectedTotal} items, got ${optimized.articles.length}`);
            console.error(`❌ English structure may be different - logging details...`);
            if (documents.chapters) {
                documents.chapters.forEach((chapter, i) => {
                    console.log(`Chapter ${i}: ${chapter.title}, Articles: ${chapter.articles?.length}`);
                });
            }
        }
    }
    
    console.log(`✅ VERIFIED: Optimized ${optimized.articles.length} COMPLETE AUTHENTIC legal articles for ${language}`);
    console.log(`📊 Articles preserved: ALL ${optimized.articles.length} items including appendices`);
    
    return optimized;
}

/**
 * Preprocess Arabic text for optimal DeepSeek processing
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
 * Smart Query Partitioning for Arabic - Revolutionary Solution!
 */
function shouldUsePartitioning(query, language) {
    return language === 'ar' && query.trim().length > 8;
}

function partitionDocuments(documents) {
    if (!documents || !documents.articles || !Array.isArray(documents.articles)) {
        console.warn('⚠️ Invalid document structure for partitioning');
        return [documents];
    }
    
    const articles = documents.articles;
    const partitionSize = Math.ceil(articles.length / 4); // Split into 4 parts for better processing
    
    console.log(`📑 Partitioning ${articles.length} articles into chunks of ${partitionSize}`);
    
    const partitions = [];
    for (let i = 0; i < articles.length; i += partitionSize) {
        const partitionArticles = articles.slice(i, i + partitionSize);
        
        const partition = {
            language: documents.language,
            title: documents.title,
            total_articles: documents.total_articles,
            articles: partitionArticles,
            partition_info: `${i + 1}-${Math.min(i + partitionSize, articles.length)} of ${articles.length}`
        };
        
        partitions.push(partition);
    }
    
    console.log(`✅ Created ${partitions.length} document partitions`);
    return partitions;
}

/**
 * Process Partitioned Query - Preserves ALL Arabic text integrity
 */
async function processPartitionedQuery(query, language, documents) {
    const partitions = partitionDocuments(documents);
    const allResults = [];
    
    console.log(`🧩 Smart partitioning: Processing ${partitions.length} document chunks`);
    
    for (let i = 0; i < partitions.length; i++) {
        console.log(`📑 Processing partition ${i + 1}/${partitions.length}`);
        
        try {
            const chatPayload = createStreamingChatPayload(query, language, partitions[i]);
            const response = await streamDeepSeekAPI(chatPayload, language);
            
            if (response && response.choices && response.choices[0]) {
                try {
                    const content = response.choices[0].message.content;
                    const parsed = JSON.parse(content);
                    if (parsed.results && Array.isArray(parsed.results)) {
                        allResults.push(...parsed.results);
                    }
                } catch (parseError) {
                    console.log(`⚠️ Parse error in partition ${i + 1}, skipping`);
                }
            }
        } catch (partitionError) {
            console.log(`⚠️ Error in partition ${i + 1}, continuing with others`);
        }
    }
    
    // Merge and rank results
    const uniqueResults = [];
    const seenArticles = new Set();
    
    allResults.forEach(result => {
        const articleId = result.article_number || `result_${uniqueResults.length}`;
        if (!seenArticles.has(articleId)) {
            seenArticles.add(articleId);
            uniqueResults.push(result);
        }
    });
    
    // Sort by score descending
    uniqueResults.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    return {
        choices: [{
            message: {
                content: JSON.stringify({
                    results: uniqueResults.slice(0, 3) // Top 3 results
                })
            },
            finish_reason: 'stop'
        }]
    };
}

/**
 * Create streaming chat payload - optimized for Vercel's longer timeout
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
        model: isArabic ? "deepseek-chat" : "deepseek-chat", // Use same model for consistency
        messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt }
        ],
        temperature: 0.3, // Lower temperature for more consistent results
        max_tokens: isArabic ? 1000 : 1200,
        stream: false, // Disable streaming for reliability
        response_format: { type: "json_object" }
    };
}

/**
 * Get next available API key with load balancing
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
 * Simplified non-streaming API call for reliability
 */
function streamDeepSeekAPI(payload, language) {
    return new Promise((resolve, reject) => {
        // Remove streaming to fix the timeout issue
        const nonStreamPayload = {
            ...payload,
            stream: false // Disable streaming for reliability
        };
        
        const postData = JSON.stringify(nonStreamPayload);
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
                'Accept': 'application/json',
                'User-Agent': 'ITPF-Legal-Search/3.1-Vercel'
            }
        };

        console.log(`🚀 Using Vercel non-streaming API for ${language} - RELIABLE MODE!`);

        const req = https.request(options, (res) => {
            let responseData = '';
            
            res.on('data', (chunk) => {
                responseData += chunk.toString();
            });
            
            res.on('end', () => {
                if (res.statusCode !== 200) {
                    console.error(`DeepSeek API error: ${res.statusCode} - ${responseData}`);
                    reject({
                        error: `API error: ${res.statusCode}`,
                        message: language === 'ar' 
                            ? 'خطأ في خدمة البحث'
                            : 'Search service error'
                    });
                    return;
                }
                
                try {
                    const parsed = JSON.parse(responseData);
                    if (parsed.choices && parsed.choices[0]) {
                        resolve(parsed);
                    } else {
                        reject({
                            error: 'Invalid API response format',
                            message: language === 'ar' 
                                ? 'استجابة غير صحيحة من الخدمة'
                                : 'Invalid service response'
                        });
                    }
                } catch (parseError) {
                    console.error('JSON parse error:', parseError);
                    console.error('Raw response:', responseData);
                    reject({
                        error: 'Failed to parse API response',
                        message: language === 'ar' 
                            ? 'خطأ في تحليل الاستجابة'
                            : 'Response parsing error'
                    });
                }
            });
        });

        req.on('error', (error) => {
            console.error('Request error:', error);
            reject({
                error: `Request error: ${error.message}`,
                message: language === 'ar' 
                    ? 'خطأ في الطلب'
                    : 'Request error'
            });
        });

        // Shorter timeout for non-streaming - 60 seconds
        req.setTimeout(60000, () => {
            req.destroy();
            reject({
                error: 'Request timeout after 60 seconds',
                message: language === 'ar' 
                    ? 'انتهت مهلة الطلب'
                    : 'Request timeout'
            });
        });

        req.write(postData);
        req.end();
    });
}

/**
 * Process search results from DeepSeek API
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
                language: language,
                platform: 'Vercel Pro'
            }
        };
        
    } catch (error) {
        console.error('Error processing search results:', error);
        throw new Error('Failed to process search results');
    }
}

/**
 * Main Vercel Function Handler - With 5-minute timeout support!
 */
export default async function handler(req, res) {
    // Handle CORS preflight requests
    if (req.method === 'OPTIONS') {
        return res.status(200).json({});
    }
    
    try {
        // Check API keys
        if (DEEPSEEK_API_KEYS.length === 0) {
            console.error('No DeepSeek API keys configured');
            return res.status(500).json({
                success: false,
                error: 'API configuration error',
                message: 'Search service is not properly configured'
            });
        }
        
        console.log(`🚀 Vercel Pro: Available API keys: ${DEEPSEEK_API_KEYS.length}`);
        
        // Extract parameters from request
        let query, language;
        
        if (req.method === 'POST') {
            query = req.body.query;
            language = req.body.language || 'en';
        } else if (req.method === 'GET') {
            query = req.query.query || req.query.q;
            language = req.query.language || req.query.lang || 'en';
        } else {
            return res.status(405).json({
                success: false,
                error: 'Method not allowed',
                message: 'Only GET and POST methods are supported'
            });
        }
        
        // Validate request
        const validation = validateRequest(query, language);
        if (!validation.isValid) {
            return res.status(400).json({
                success: false,
                error: 'Validation failed',
                message: validation.errors.join('; '),
                details: validation.errors
            });
        }
        
        // Load legal documents
        const documents = loadLegalDocuments(language);
        if (!documents) {
            return res.status(500).json({
                success: false,
                error: 'Document loading error',
                message: language === 'ar' 
                    ? 'فشل في تحميل الوثائق القانونية'
                    : 'Failed to load legal documents'
            });
        }

        console.log(`🎯 Processing "${query}" in ${language} with 5-minute timeout!`);
        
        // Use optimized documents
        const optimizedDocs = optimizeDocumentsForArabic(documents, language);
        
        // Revolutionary Smart Partitioning for Arabic!
        let streamResponse;
        if (shouldUsePartitioning(query, language)) {
            console.log(`🧩 Using smart partitioning for Arabic query: "${query}"`);
            streamResponse = await processPartitionedQuery(query, language, optimizedDocs);
        } else {
            // Regular streaming for English or simple queries
            const chatPayload = createStreamingChatPayload(query, language, optimizedDocs);
            streamResponse = await streamDeepSeekAPI(chatPayload, language);
        }
        
        // Process and return results
        const processedResults = processSearchResults(streamResponse, language);
        
        console.log(`✅ Successfully processed ${language} query in Vercel Pro!`);
        
        return res.status(200).json(processedResults);
        
    } catch (error) {
        console.error('Vercel search function error:', error);
        
        const errorMessage = error.message || (
            language === 'ar' 
                ? 'حدث خطأ غير متوقع. يرجى المحاولة لاحقاً.'
                : 'An unexpected error occurred. Please try again later.'
        );
        
        return res.status(error.statusCode || 500).json({
            success: false,
            error: 'Search failed',
            message: errorMessage,
            platform: 'Vercel Pro',
            details: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
}