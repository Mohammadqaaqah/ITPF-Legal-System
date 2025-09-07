/**
 * Rebuild complete Arabic JSON with full text from arabic.txt source
 * This fixes the truncation issue in Article 114 and other articles
 */

const fs = require('fs');
const path = require('path');

// Read the original complete Arabic text
const arabicText = fs.readFileSync('arabic.txt', 'utf8');

// Read existing JSON to preserve structure
const existingJson = JSON.parse(fs.readFileSync('api/arabic_legal_rules_clean.json', 'utf8'));

console.log('🔧 Starting complete JSON rebuild...');

// Function to extract full article content from original text
function extractArticleFromOriginal(articleNumber) {
    const articlePattern = `**المادة ${articleNumber}:`;
    const nextArticlePattern = `**المادة ${articleNumber + 1}:`;
    
    const startIndex = arabicText.indexOf(articlePattern);
    if (startIndex === -1) {
        console.warn(`⚠️ Article ${articleNumber} not found in original text`);
        return null;
    }
    
    const nextIndex = arabicText.indexOf(nextArticlePattern);
    const endIndex = nextIndex === -1 ? arabicText.length : nextIndex;
    
    const fullText = arabicText.substring(startIndex, endIndex).trim();
    
    // Remove the header pattern and get clean content
    const cleanContent = fullText.replace(articlePattern, '').trim();
    const titleMatch = cleanContent.match(/^([^\n]+)/);
    const title = titleMatch ? titleMatch[1].trim() : '';
    
    // Get content after title
    const content = cleanContent.replace(title, '').trim();
    
    return { title, content, fullLength: fullText.length };
}

// Update all articles with complete content
console.log('📝 Rebuilding articles with complete content...');

existingJson.articles = existingJson.articles.map(article => {
    const articleNumber = article.article_number;
    const completeArticle = extractArticleFromOriginal(articleNumber);
    
    if (completeArticle) {
        const originalLength = article.content?.length || 0;
        const newLength = completeArticle.content.length;
        
        console.log(`✅ Article ${articleNumber}: ${originalLength} → ${newLength} chars`);
        
        if (articleNumber === 114) {
            console.log(`🎯 Article 114 FIXED: ${originalLength} → ${newLength} chars`);
            console.log(`   Title: ${completeArticle.title}`);
            console.log(`   Content preview: ${completeArticle.content.substring(0, 100)}...`);
            console.log(`   Content ending: ...${completeArticle.content.substring(completeArticle.content.length - 100)}`);
        }
        
        return {
            ...article,
            title: completeArticle.title || article.title,
            content: completeArticle.content,
            original_length: newLength
        };
    }
    
    return article;
});

// Update metadata
existingJson.metadata.rebuild_info = {
    rebuilt_at: new Date().toISOString(),
    source: 'arabic.txt',
    reason: 'Fix article truncation, especially Article 114'
};

// Write the complete JSON
const outputPath = 'api/arabic_legal_rules_complete_fixed.json';
fs.writeFileSync(outputPath, JSON.stringify(existingJson, null, 2), 'utf8');

console.log(`✅ Complete JSON written to: ${outputPath}`);
console.log(`📊 Total articles: ${existingJson.articles.length}`);

// Verify Article 114
const article114 = existingJson.articles.find(a => a.article_number === 114);
if (article114) {
    console.log(`\n🎯 ARTICLE 114 VERIFICATION:`);
    console.log(`   Length: ${article114.content.length} chars`);
    console.log(`   Title: ${article114.title}`);
    console.log(`   Starts with: ${article114.content.substring(0, 80)}...`);
    console.log(`   Ends with: ...${article114.content.substring(article114.content.length - 80)}`);
}

console.log('\n🎉 JSON rebuild complete!');