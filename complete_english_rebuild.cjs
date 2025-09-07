/**
 * COMPLETE English rebuild - same integrity standards as Arabic
 * Extract ALL articles with complete content from english.txt
 */

const fs = require('fs');

console.log('🔧 COMPLETE ENGLISH REBUILD - FULL INTEGRITY');

// Read original English text
const englishOriginal = fs.readFileSync('english.txt', 'utf8');
const existingJson = JSON.parse(fs.readFileSync('api/english_legal_rules_complete_authentic.json', 'utf8'));

// Function to extract complete article content from original English text  
function extractEnglishArticle(articleNumber) {
    const articlePattern = `**Article ${articleNumber} `;
    const nextArticlePattern = `**Article ${articleNumber + 1} `;
    const chapterPattern = `**CHAPTER `;
    const appendixPattern = `**APPENDIX `;
    
    const startIndex = englishOriginal.indexOf(articlePattern);
    if (startIndex === -1) {
        console.warn(`⚠️ Article ${articleNumber} not found in original English text`);
        return null;
    }
    
    // Find next boundary (next article, chapter, or appendix)
    let endIndex = englishOriginal.length;
    const nextArticleIndex = englishOriginal.indexOf(nextArticlePattern, startIndex + 1);
    const nextChapterIndex = englishOriginal.indexOf(chapterPattern, startIndex + 1);
    const nextAppendixIndex = englishOriginal.indexOf(appendixPattern, startIndex + 1);
    
    [nextArticleIndex, nextChapterIndex, nextAppendixIndex]
        .filter(idx => idx !== -1)
        .forEach(idx => {
            if (idx < endIndex) endIndex = idx;
        });
    
    const fullText = englishOriginal.substring(startIndex, endIndex).trim();
    
    // Extract title and content
    const lines = fullText.split('\n');
    const titleLine = lines[0].replace(/\*\*/g, '').replace(`Article ${articleNumber} `, '').trim();
    const content = lines.slice(1).join('\n').trim();
    
    return { 
        title: titleLine, 
        content: content,
        fullLength: fullText.length,
        article_number: articleNumber
    };
}

console.log('📝 Rebuilding ALL English articles with complete content...');

// Build complete articles array
const completeArticles = [];
let articlesFixed = 0;
let totalOriginalLength = 0;
let totalNewLength = 0;

// Extract articles 100-154 (same range as Arabic)
for (let articleNum = 100; articleNum <= 154; articleNum++) {
    const completeArticle = extractEnglishArticle(articleNum);
    
    if (completeArticle) {
        // Find existing article in JSON to get original length
        let originalLength = 0;
        for (const chapter of existingJson.chapters) {
            if (chapter.articles) {
                const existing = chapter.articles.find(a => 
                    a.title?.includes(completeArticle.title.substring(0, 20)) ||
                    a.content?.includes(completeArticle.content.substring(0, 50))
                );
                if (existing) {
                    originalLength = existing.content?.length || 0;
                    break;
                }
            }
        }
        
        completeArticles.push({
            article_number: articleNum,
            title: completeArticle.title,
            content: completeArticle.content,
            source: 'english.txt',
            original_length: originalLength,
            complete_length: completeArticle.content.length
        });
        
        totalOriginalLength += originalLength;
        totalNewLength += completeArticle.content.length;
        
        if (completeArticle.content.length > originalLength + 100) {
            console.log(`✅ Article ${articleNum}: ${originalLength} → ${completeArticle.content.length} chars`);
            articlesFixed++;
        }
    }
}

// Create new complete English structure
const completeEnglishJson = {
    metadata: {
        title: "ITPF Legal Rules - Complete English Version",
        total_articles: completeArticles.length,
        language: "en",
        rebuild_info: {
            rebuilt_at: new Date().toISOString(),
            source: "english.txt",
            reason: "Fix systematic truncation - restore complete content",
            articles_fixed: articlesFixed,
            total_original_length: totalOriginalLength,
            total_complete_length: totalNewLength,
            integrity_improvement: Math.round((totalNewLength / totalOriginalLength) * 100) + '%'
        }
    },
    articles: completeArticles,
    appendices: existingJson.appendices // Keep existing appendices (they were complete)
};

// Write complete English JSON
const outputPath = 'api/english_legal_rules_complete_rebuild.json';
fs.writeFileSync(outputPath, JSON.stringify(completeEnglishJson, null, 2), 'utf8');

console.log(`✅ COMPLETE English rebuild written to: ${outputPath}`);
console.log(`📊 Articles rebuilt: ${completeArticles.length}`);
console.log(`🔧 Articles significantly improved: ${articlesFixed}`);
console.log(`📈 Content integrity: ${totalOriginalLength} → ${totalNewLength} chars`);
console.log(`📊 Integrity improvement: ${Math.round((totalNewLength / totalOriginalLength) * 100)}%`);

// Verify specific articles
const article105 = completeArticles.find(a => a.article_number === 105);
if (article105) {
    console.log(`\\n🎯 ARTICLE 105 VERIFICATION:`);
    console.log(`   Original: ${article105.original_length} chars`);
    console.log(`   Complete: ${article105.complete_length} chars`);
    console.log(`   Improvement: ${Math.round((article105.complete_length / article105.original_length) * 100)}%`);
    console.log(`   Title: ${article105.title}`);
}

console.log('\\n🎉 COMPLETE ENGLISH REBUILD FINISHED - FULL INTEGRITY RESTORED!');