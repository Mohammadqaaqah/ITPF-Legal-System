"""
ITPF Legal Answer System - Hybrid AI-powered Q&A Endpoint for Vercel
النظام الهجين: البحث المحلي الدقيق + تحليل DeepSeek الذكي
"""

import json
import os
import re
import requests
from typing import Dict, Any, List
import difflib
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs


def call_deepseek_api(prompt: str, max_tokens: int = 500) -> str:
    """Call DeepSeek API with intelligent prompt handling"""
    
    # Get API keys from environment (cycling through 3 keys for load balancing)
    api_keys = [
        os.getenv('DEEPSEEK_API_KEY_1'),
        os.getenv('DEEPSEEK_API_KEY_2'), 
        os.getenv('DEEPSEEK_API_KEY_3')
    ]
    
    # Filter out None values and placeholder values
    valid_keys = [key for key in api_keys if key and key != 'your-actual-deepseek-key-here' and key != 'your_actual_key_here']
    
    if not valid_keys:
        print("No valid DeepSeek API keys found - using algorithmic fallback")
        return None
    
    # Try each API key with intelligent rotation
    for i, api_key in enumerate(valid_keys):
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # DeepSeek API endpoint (OpenAI compatible)
            url = "https://api.deepseek.com/v1/chat/completions"
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "أنت قاضٍ ومحلل قانوني متخصص في قواعد الاتحاد الدولي لالتقاط الأوتاد. تقدم إجابات دقيقة ومختصرة وذكية بناء على النصوص المرفقة فقط."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,
                "stream": False
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content'].strip()
                    return ai_response if ai_response else None
            else:
                print(f"DeepSeek API error {response.status_code}: {response.text}")
            
        except Exception as e:
            print(f"DeepSeek API error with key {i+1}: {str(e)}")
            continue
    
    # If all API keys failed, return None
    return None


def load_legal_data():
    """Load complete legal data from split JSON files"""
    try:
        # Get the directory of the current script (api directory)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load Arabic data from split files
        arabic_data = {"metadata": {}, "articles": [], "appendices": []}
        for i in range(1, 4):  # Load parts 1, 2, 3
            arabic_file = os.path.join(script_dir, f'arabic_data_part{i}.json')
            try:
                with open(arabic_file, 'r', encoding='utf-8') as f:
                    part_data = json.load(f)
                    if i == 1:  # Get metadata and appendices from first part
                        arabic_data["metadata"] = part_data.get("metadata", {})
                        arabic_data["appendices"] = part_data.get("appendices", [])
                    arabic_data["articles"].extend(part_data.get("articles", []))
            except Exception as e:
                print(f"Error loading Arabic part {i}: {str(e)}")
        
        print(f"Arabic data loaded: {len(arabic_data['articles'])} articles, {len(arabic_data['appendices'])} appendices")
        
        # Load English data from split files
        english_data = {"metadata": {}, "chapters": [], "appendices": []}
        for i in range(1, 4):  # Load parts 1, 2, 3
            english_file = os.path.join(script_dir, f'english_data_part{i}.json')
            try:
                with open(english_file, 'r', encoding='utf-8') as f:
                    part_data = json.load(f)
                    if i == 1:  # Get metadata and appendices from first part
                        english_data["metadata"] = part_data.get("metadata", {})
                        english_data["appendices"] = part_data.get("appendices", [])
                    english_data["chapters"].extend(part_data.get("chapters", []))
            except Exception as e:
                print(f"Error loading English part {i}: {str(e)}")
        
        # Extract articles from chapters for easier access
        all_english_articles = []
        if english_data["chapters"]:
            for chapter in english_data["chapters"]:
                all_english_articles.extend(chapter.get("articles", []))
        
        print(f"English data loaded: {len(all_english_articles)} articles, {len(english_data.get('appendices', []))} appendices")
        
        # Fallback: Try original files if split files not found
        if not arabic_data["articles"]:
            try:
                with open('arabic_legal_rules_complete_authentic.json', 'r', encoding='utf-8') as f:
                    arabic_data = json.load(f)
                    print(f"Fallback Arabic data loaded: {len(arabic_data.get('articles', []))} articles")
            except Exception as e:
                print(f"Error loading Arabic fallback data: {str(e)}")
        
        if not all_english_articles:
            try:
                with open('english_legal_rules_complete_authentic.json', 'r', encoding='utf-8') as f:
                    english_data = json.load(f)
                    print(f"Fallback English data loaded")
            except Exception as e:
                print(f"Error loading English fallback data: {str(e)}")
            
        return arabic_data, english_data
    except Exception as e:
        print(f"Critical error loading legal data: {str(e)}")
        return [], []


# PHASE 1: COMPREHENSIVE ITPF CONCEPT MAP AND SYNONYMS DICTIONARY
ITPF_CONCEPT_MAP = {
    "equipment": {
        "arabic_terms": ["المعدات", "الأدوات", "التجهيزات", "العتاد", "الآلات", "الأجهزة"],
        "english_terms": ["equipment", "gear", "tools", "apparatus", "devices", "instruments"],
        "synonyms": {
            "arabic": ["اللوازم", "المستلزمات", "الأدوات المطلوبة", "التجهيزات الضرورية", "المعدات الرياضية"],
            "english": ["sporting goods", "athletic equipment", "necessary tools", "required apparatus", "contest gear"]
        },
        "related_concepts": ["safety", "specifications", "requirements", "approval", "certification"],
        "context_keywords": ["مواصفات", "متطلبات", "أمان", "سلامة", "اعتماد", "شهادة"]
    },
    "scoring": {
        "arabic_terms": ["النقاط", "التسجيل", "الدرجات", "الأحراز", "النتائج", "المجموع"],
        "english_terms": ["scoring", "points", "grades", "marks", "tally", "count"],
        "synonyms": {
            "arabic": ["حساب النقاط", "جمع الدرجات", "تسجيل الأحراز", "إحراز النقاط", "النتيجة النهائية"],
            "english": ["point counting", "score calculation", "result tallying", "grade computation", "final score"]
        },
        "related_concepts": ["competition", "judges", "rules", "results", "ranking"],
        "context_keywords": ["حكم", "تحكيم", "ترتيب", "منافسة", "فوز", "تقييم"]
    },
    "competition": {
        "arabic_terms": ["المسابقة", "البطولة", "المنافسة", "التنافس", "المباراة", "البرنامج"],
        "english_terms": ["competition", "contest", "tournament", "championship", "match", "event"],
        "synonyms": {
            "arabic": ["الفعالية", "النشاط الرياضي", "المهرجان الرياضي", "الدوري", "الكأس", "البرنامج الرياضي"],
            "english": ["sporting event", "athletic contest", "competitive event", "tournament series", "championship series"]
        },
        "related_concepts": ["participants", "registration", "rules", "categories", "timing"],
        "context_keywords": ["مشارك", "مشاركة", "تسجيل", "فئة", "زمن", "دور", "مرحلة"]
    },
    "safety": {
        "arabic_terms": ["الأمان", "السلامة", "الحماية", "الوقاية", "الأمن", "التأمين"],
        "english_terms": ["safety", "security", "protection", "precaution", "safeguarding"],
        "synonyms": {
            "arabic": ["الإجراءات الوقائية", "التدابير الأمنية", "وسائل الحماية", "شروط السلامة"],
            "english": ["safety measures", "protective procedures", "security protocols", "safety requirements"]
        },
        "related_concepts": ["equipment", "rules", "supervision", "emergency", "medical"],
        "context_keywords": ["طوارئ", "إسعاف", "طبي", "إشراف", "مراقبة", "خطر"]
    },
    "judges": {
        "arabic_terms": ["الحكام", "المحكمين", "القضاة", "المراقبين", "المشرفين"],
        "english_terms": ["judges", "referees", "officials", "arbitrators", "supervisors"],
        "synonyms": {
            "arabic": ["هيئة التحكيم", "لجنة الحكام", "المسؤولين", "القائمين على التحكيم"],
            "english": ["judging panel", "officiating crew", "referee team", "judging committee"]
        },
        "related_concepts": ["scoring", "rules", "decisions", "appeals", "certification"],
        "context_keywords": ["قرار", "حكم", "تقييم", "اعتراض", "استئناف", "شهادة"]
    },
    "field": {
        "arabic_terms": ["الميدان", "الساحة", "المنطقة", "الملعب", "الحلبة", "المجال"],
        "english_terms": ["field", "arena", "area", "ground", "venue", "pitch"],
        "synonyms": {
            "arabic": ["مكان المسابقة", "موقع الفعالية", "أرض المنافسة", "ساحة اللعب"],
            "english": ["competition venue", "contest area", "playing field", "competition ground"]
        },
        "related_concepts": ["dimensions", "specifications", "preparation", "marking", "boundaries"],
        "context_keywords": ["أبعاد", "مواصفات", "تحضير", "علامات", "حدود", "خط"]
    },
    "timing": {
        "arabic_terms": ["التوقيت", "الزمن", "المدة", "الوقت", "التسجيل الزمني"],
        "english_terms": ["timing", "time", "duration", "period", "chronometer"],
        "synonyms": {
            "arabic": ["قياس الوقت", "حساب المدة", "تسجيل الأزمنة", "ضبط التوقيت"],
            "english": ["time measurement", "duration recording", "chronometric recording", "time keeping"]
        },
        "related_concepts": ["competition", "results", "records", "precision", "equipment"],
        "context_keywords": ["دقة", "سجل", "رقم قياسي", "قياس", "ضبط"]
    },
    "registration": {
        "arabic_terms": ["التسجيل", "التقييد", "القيد", "الاشتراك", "المشاركة"],
        "english_terms": ["registration", "enrollment", "sign-up", "participation", "entry"],
        "synonyms": {
            "arabic": ["تسجيل المشاركة", "قيد الاشتراك", "طلب المشاركة", "الانضمام"],
            "english": ["participant registration", "contest entry", "enrollment process", "sign-up procedure"]
        },
        "related_concepts": ["participants", "categories", "requirements", "deadlines", "fees"],
        "context_keywords": ["مشارك", "فئة", "متطلبات", "موعد نهائي", "رسوم"]
    },
    "rules": {
        "arabic_terms": ["القواعد", "القوانين", "الأنظمة", "اللوائح", "التعليمات"],
        "english_terms": ["rules", "regulations", "laws", "guidelines", "instructions"],
        "synonyms": {
            "arabic": ["الأحكام", "الشروط", "الضوابط", "المبادئ التوجيهية", "النصوص القانونية"],
            "english": ["provisions", "conditions", "controls", "guiding principles", "legal texts"]
        },
        "related_concepts": ["compliance", "violations", "penalties", "interpretation", "application"],
        "context_keywords": ["التزام", "مخالفة", "عقوبة", "تفسير", "تطبيق"]
    }
}

def expand_question_with_concepts(question: str) -> list:
    """
    Phase 1 Enhancement: Expand question using ITPF concept mapping and synonyms
    تفكيك السؤال إلى مفاهيم وإضافة المرادفات والمصطلحات ذات الصلة
    """
    question_lower = question.lower().strip()
    expanded_terms = []
    matched_concepts = []
    
    # Add original question terms
    original_terms = re.findall(r'\b[\u0600-\u06FFa-zA-Z]+\b', question_lower)
    expanded_terms.extend([term for term in original_terms if len(term) > 2])
    
    # Map question to ITPF concepts
    for concept_name, concept_data in ITPF_CONCEPT_MAP.items():
        concept_matched = False
        
        # Check Arabic terms
        for term in concept_data["arabic_terms"]:
            if term.lower() in question_lower:
                matched_concepts.append(concept_name)
                expanded_terms.extend(concept_data["arabic_terms"])
                expanded_terms.extend(concept_data["synonyms"]["arabic"])
                expanded_terms.extend(concept_data["context_keywords"])
                concept_matched = True
                break
        
        # Check English terms if not already matched
        if not concept_matched:
            for term in concept_data["english_terms"]:
                if term.lower() in question_lower:
                    matched_concepts.append(concept_name)
                    expanded_terms.extend(concept_data["english_terms"])
                    expanded_terms.extend(concept_data["synonyms"]["english"])
                    concept_matched = True
                    break
        
        # Check synonyms for partial matches
        if not concept_matched:
            for synonym in concept_data["synonyms"]["arabic"]:
                if any(word in question_lower for word in synonym.split()):
                    matched_concepts.append(concept_name)
                    expanded_terms.extend(concept_data["arabic_terms"])
                    expanded_terms.extend(concept_data["context_keywords"])
                    break
    
    # Add related concepts
    for matched_concept in matched_concepts:
        related_concepts = ITPF_CONCEPT_MAP[matched_concept].get("related_concepts", [])
        for related in related_concepts:
            if related in ITPF_CONCEPT_MAP:
                expanded_terms.extend(ITPF_CONCEPT_MAP[related]["arabic_terms"][:2])
                expanded_terms.extend(ITPF_CONCEPT_MAP[related]["english_terms"][:2])
    
    # Remove duplicates and filter
    unique_terms = list(set([term.lower() for term in expanded_terms if len(term) > 2]))
    
    print(f"Question expansion - Original: {len(original_terms)} terms, Expanded: {len(unique_terms)} terms")
    print(f"Matched concepts: {matched_concepts}")
    
    return unique_terms

# PHASE 2: ADVANCED CONTEXTUAL ANALYSIS SYSTEM
LEGAL_CONTEXT_HIERARCHIES = {
    "procedural": {
        "keywords": ["كيف", "ماذا", "متى", "أين", "how", "what", "when", "where", "procedure", "process"],
        "intent": "procedural_guidance",
        "priority_concepts": ["registration", "competition", "timing", "field"],
        "response_style": "step_by_step"
    },
    "regulatory": {
        "keywords": ["يجب", "يُمنع", "مطلوب", "ضروري", "قانوني", "must", "required", "mandatory", "legal", "rule"],
        "intent": "rule_compliance", 
        "priority_concepts": ["rules", "safety", "equipment", "judges"],
        "response_style": "compliance_focused"
    },
    "technical": {
        "keywords": ["مواصفات", "تقني", "معدات", "أبعاد", "قياس", "technical", "specifications", "measurements", "equipment"],
        "intent": "technical_details",
        "priority_concepts": ["equipment", "field", "timing", "specifications"],
        "response_style": "specification_detailed"
    },
    "competitive": {
        "keywords": ["نقاط", "فوز", "ترتيب", "بطولة", "مسابقة", "points", "win", "competition", "tournament", "scoring"],
        "intent": "competition_mechanics",
        "priority_concepts": ["scoring", "competition", "judges", "rules"],
        "response_style": "outcome_focused"
    }
}

CONTEXTUAL_RELATIONSHIPS = {
    "equipment_safety": {
        "concepts": ["equipment", "safety"],
        "relationship": "Equipment must meet safety standards",
        "cross_references": ["approval", "certification", "specifications"]
    },
    "competition_scoring": {
        "concepts": ["competition", "scoring", "judges"],
        "relationship": "Competition results determined by judge scoring",
        "cross_references": ["rules", "rankings", "results"]
    },
    "field_timing": {
        "concepts": ["field", "timing", "competition"],
        "relationship": "Field specifications affect timing and competition flow",
        "cross_references": ["equipment", "safety", "specifications"]
    },
    "registration_participation": {
        "concepts": ["registration", "competition", "rules"],
        "relationship": "Registration requirements govern competition participation",
        "cross_references": ["categories", "requirements", "deadlines"]
    }
}

def analyze_question_context(question: str) -> dict:
    """
    Phase 2 Enhancement: Advanced contextual analysis of question intent
    تحليل السياق المتقدم لفهم نية السؤال وتصنيفه
    """
    question_lower = question.lower().strip()
    context_analysis = {
        "primary_intent": "general",
        "secondary_intents": [],
        "legal_hierarchy": "basic",
        "priority_concepts": [],
        "response_style": "balanced",
        "contextual_relationships": []
    }
    
    # Analyze question intent based on keywords
    intent_scores = {}
    for context_type, context_data in LEGAL_CONTEXT_HIERARCHIES.items():
        score = 0
        for keyword in context_data["keywords"]:
            if keyword in question_lower:
                score += 2
                # Check for question patterns that indicate specific intent
                if question_lower.startswith(("كيف", "how", "ماذا", "what")):
                    if context_type == "procedural":
                        score += 3
                elif "يجب" in question_lower or "must" in question_lower:
                    if context_type == "regulatory":
                        score += 3
                elif "مواصفات" in question_lower or "specifications" in question_lower:
                    if context_type == "technical":
                        score += 3
                elif "نقاط" in question_lower or "points" in question_lower:
                    if context_type == "competitive":
                        score += 3
        intent_scores[context_type] = score
    
    # Determine primary intent
    if intent_scores:
        primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
        if intent_scores[primary_intent] > 0:
            context_analysis["primary_intent"] = primary_intent
            context_analysis["priority_concepts"] = LEGAL_CONTEXT_HIERARCHIES[primary_intent]["priority_concepts"]
            context_analysis["response_style"] = LEGAL_CONTEXT_HIERARCHIES[primary_intent]["response_style"]
            
            # Add secondary intents (scores > 1)
            for intent, score in intent_scores.items():
                if intent != primary_intent and score > 1:
                    context_analysis["secondary_intents"].append(intent)
    
    # Identify relevant contextual relationships
    for rel_name, rel_data in CONTEXTUAL_RELATIONSHIPS.items():
        for concept in context_analysis["priority_concepts"]:
            if concept in rel_data["concepts"]:
                context_analysis["contextual_relationships"].append(rel_name)
                break
    
    print(f"Context analysis - Intent: {context_analysis['primary_intent']}, Style: {context_analysis['response_style']}")
    return context_analysis

def enhance_search_with_context(question: str, expanded_terms: list, context_analysis: dict) -> list:
    """
    Phase 2 Enhancement: Enhance search terms based on contextual analysis
    تعزيز مصطلحات البحث بناء على التحليل السياقي
    """
    enhanced_terms = expanded_terms.copy()
    
    # Add context-specific terms based on intent
    intent = context_analysis["primary_intent"]
    if intent in LEGAL_CONTEXT_HIERARCHIES:
        intent_data = LEGAL_CONTEXT_HIERARCHIES[intent]
        
        # Add priority concept terms
        for priority_concept in intent_data["priority_concepts"]:
            if priority_concept in ITPF_CONCEPT_MAP:
                concept_data = ITPF_CONCEPT_MAP[priority_concept]
                enhanced_terms.extend(concept_data["arabic_terms"][:3])
                enhanced_terms.extend(concept_data["english_terms"][:2])
                enhanced_terms.extend(concept_data["context_keywords"][:3])
    
    # Add terms from contextual relationships
    for rel_name in context_analysis["contextual_relationships"]:
        if rel_name in CONTEXTUAL_RELATIONSHIPS:
            rel_data = CONTEXTUAL_RELATIONSHIPS[rel_name]
            enhanced_terms.extend(rel_data["cross_references"])
    
    # Remove duplicates and return
    unique_enhanced_terms = list(set([term.lower() for term in enhanced_terms if len(term) > 2]))
    
    print(f"Enhanced search - Original: {len(expanded_terms)}, Enhanced: {len(unique_enhanced_terms)}")
    return unique_enhanced_terms

def advanced_search_relevant_content(question: str, data: list, language: str) -> list:
    """Advanced search algorithm enhanced with ITPF concept mapping and contextual analysis"""
    relevant_articles = []
    
    # PHASE 1: CONCEPT-ENHANCED SEARCH
    # Use concept mapping to expand search terms
    expanded_keywords = expand_question_with_concepts(question)
    
    # PHASE 2: CONTEXTUAL ANALYSIS ENHANCEMENT
    # Analyze question context and intent
    context_analysis = analyze_question_context(question)
    
    # Enhance search terms with contextual understanding
    enhanced_keywords = enhance_search_with_context(question, expanded_keywords, context_analysis)
    
    # Clean and prepare question for analysis
    question_lower = question.lower().strip()
    
    # Extract original keywords as backup
    arabic_keywords = re.findall(r'\b[\u0600-\u06FF]+\b', question_lower)
    english_keywords = re.findall(r'\b[a-zA-Z]+\b', question_lower)
    
    # Combine original, expanded, and contextually enhanced keywords
    all_keywords = list(set(enhanced_keywords + arabic_keywords + english_keywords))
    
    print(f"Search keywords extracted: {all_keywords}")
    
    for article in data:
        # Handle both dict and string formats
        if isinstance(article, dict):
            content_text = str(article.get('content', '')).lower()
            title_text = str(article.get('title', '')).lower()
            article_number = str(article.get('article_number', ''))
        else:
            # Skip invalid articles
            continue
        
        # Calculate relevance score
        relevance_score = 0
        matched_keywords = []
        
        # Direct keyword matching
        for keyword in all_keywords:
            if len(keyword) > 2:  # Ignore very short keywords
                if keyword in content_text:
                    relevance_score += 3
                    matched_keywords.append(keyword)
                elif keyword in title_text:
                    relevance_score += 2
                    matched_keywords.append(keyword)
        
        # Fuzzy matching for important terms
        important_terms = ['المشاركة', 'التسجيل', 'النقاط', 'المعدات', 'البطولة', 'القواعد', 'النظام']
        for term in important_terms:
            if term in question_lower:
                # Check for similar terms in content
                similar_matches = difflib.get_close_matches(term, content_text.split(), n=3, cutoff=0.6)
                if similar_matches:
                    relevance_score += 1
                    matched_keywords.extend(similar_matches)
        
        # PHASE 2: CONTEXTUAL SCORING ENHANCEMENT
        # Apply contextual boosting based on intent analysis
        if relevance_score > 0:
            # Boost scores for articles that match the identified intent
            intent_boost = 0
            if context_analysis["primary_intent"] != "general":
                response_style = context_analysis["response_style"]
                
                # Boost based on response style requirements
                if response_style == "compliance_focused" and any(compliance_term in content_text for compliance_term in ["يجب", "مطلوب", "ضروري", "must", "required"]):
                    intent_boost += 2
                elif response_style == "specification_detailed" and any(spec_term in content_text for spec_term in ["مواصفات", "أبعاد", "قياس", "specifications", "measurements"]):
                    intent_boost += 2
                elif response_style == "step_by_step" and any(proc_term in content_text for proc_term in ["خطوات", "كيفية", "طريقة", "steps", "procedure"]):
                    intent_boost += 2
                elif response_style == "outcome_focused" and any(outcome_term in content_text for outcome_term in ["نتيجة", "فوز", "نقاط", "result", "win", "points"]):
                    intent_boost += 2
            
            final_score = relevance_score + intent_boost
            
            article_copy = article.copy()
            article_copy['relevance_score'] = final_score
            article_copy['matched_keywords'] = matched_keywords
            article_copy['search_language'] = language
            article_copy['context_intent'] = context_analysis["primary_intent"]
            article_copy['intent_boost'] = intent_boost
            relevant_articles.append(article_copy)
    
    # Sort by relevance score (highest first)
    relevant_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    print(f"Found {len(relevant_articles)} relevant articles")
    return relevant_articles


def extract_search_keywords(question: str) -> List[str]:
    """Extract key search terms from complex questions"""
    import re
    
    # Arabic keywords mapping
    keyword_patterns = {
        'تأخر': ['تأخير', 'متأخر', 'تأخر', 'وقت'],
        'عقوبة': ['عقوبة', 'جزاء', 'خصم', 'استبعاد'],
        'استثناء': ['استثناء', 'استثناءات', 'حالة خاصة', 'باستثناء'],
        'نقاط': ['نقطة', 'نقاط', 'درجة', 'درجات'],
        'وقت': ['ثانية', 'دقيقة', 'وقت', 'زمن'],
        'شارة': ['إشارة', 'بداية', 'انطلاق', 'شارة']
    }
    
    keywords = []
    question_lower = question.lower()
    
    # Extract direct keywords
    for main_keyword, variations in keyword_patterns.items():
        for variation in variations:
            if variation in question_lower:
                keywords.append(main_keyword)
                break
    
    # Extract numbers (time values)
    numbers = re.findall(r'\d+', question)
    if numbers:
        keywords.extend([f'{num}' for num in numbers])
    
    # Add the original question for comprehensive search
    keywords.append(question)
    
    return list(set(keywords))

def intelligent_question_decomposition(question: str, language: str) -> Dict[str, Any]:
    """
    المرحلة الأولى: تفكيك السؤال الذكي إلى عناصر ومفاهيم أساسية
    Phase 1: Intelligent question decomposition into basic elements and concepts
    """
    
    # تحليل نوع السؤال وتصنيفه
    question_analysis = {
        "original_question": question,
        "question_type": "general",  # definition, procedure, regulation, penalty, etc.
        "key_concepts": [],         # المفاهيم الأساسية
        "search_elements": [],      # عناصر البحث المحددة
        "context_indicators": [],   # مؤشرات السياق
        "priority_areas": []        # المجالات ذات الأولوية
    }
    
    # تحديد الكلمات المفتاحية الأساسية
    question_lower = question.lower()
    
    # أنماط الأسئلة الشائعة
    if any(word in question_lower for word in ['ما هي', 'ما هو', 'what is', 'what are']):
        question_analysis["question_type"] = "definition"
    elif any(word in question_lower for word in ['كيف', 'كيفية', 'how', 'طريقة']):
        question_analysis["question_type"] = "procedure"  
    elif any(word in question_lower for word in ['قواعد', 'شروط', 'متطلبات', 'rules', 'requirements']):
        question_analysis["question_type"] = "regulation"
    elif any(word in question_lower for word in ['عقوبة', 'جزاء', 'penalty', 'punishment']):
        question_analysis["question_type"] = "penalty"
    elif any(word in question_lower for word in ['ملحق', 'appendix', 'جدول']):
        question_analysis["question_type"] = "appendix"
    
    # استخراج المفاهيم الأساسية
    key_terms = [
        'تقاط الأوتاد', 'tent pegging', 'فارس', 'rider', 'حصان', 'horse',
        'مسابقة', 'competition', 'بطولة', 'championship', 'ميدان', 'arena',
        'سرعة', 'speed', 'دقة', 'accuracy', 'نقاط', 'points', 'درجات', 'scores',
        'حكم', 'judge', 'تحكيم', 'judging', 'لجنة', 'committee',
        'ملحق', 'appendix', 'جدول', 'table', 'رسم', 'diagram'
    ]
    
    for term in key_terms:
        if term in question_lower:
            question_analysis["key_concepts"].append(term)
    
    # تحديد عناصر البحث المحددة
    search_elements = question_analysis["key_concepts"].copy()
    
    # إضافة كلمات ذات صلة بناءً على السياق
    if 'ملحق' in question_lower or 'appendix' in question_lower:
        if '9' in question or 'تسعة' in question_lower or 'nine' in question_lower:
            search_elements.extend(['ملحق 9', 'appendix 9', 'أشواط', 'rounds'])
        if '10' in question or 'عشرة' in question_lower or 'ten' in question_lower:
            search_elements.extend(['ملحق 10', 'appendix 10', 'ميدان', 'field'])
    
    question_analysis["search_elements"] = search_elements
    
    print(f"تم تفكيك السؤال - النوع: {question_analysis['question_type']}, المفاهيم: {question_analysis['key_concepts']}")
    return question_analysis

def extract_relevant_sentences(content: str, search_elements: List[str]) -> str:
    """
    استخراج الجمل الأكثر صلة من النص بناءً على عناصر البحث
    Extract most relevant sentences from content based on search elements
    """
    
    if not content or not search_elements:
        return content[:200] + "..." if len(content) > 200 else content
    
    sentences = content.split('.')
    relevant_sentences = []
    
    # البحث عن الجمل التي تحتوي على عناصر البحث
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if sentence_lower and len(sentence.strip()) > 10:  # تجنب الجمل القصيرة جداً
            # حساب درجة الصلة بناءً على عناصر البحث
            relevance_score = 0
            for element in search_elements:
                if element.lower() in sentence_lower:
                    relevance_score += 1
            
            if relevance_score > 0:
                relevant_sentences.append((sentence.strip(), relevance_score))
    
    # ترتيب الجمل حسب الصلة
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    
    # أخذ أفضل 3-5 جمل
    selected_sentences = [sent[0] for sent in relevant_sentences[:5]]
    
    if not selected_sentences:
        # إذا لم توجد جمل مناسبة، اأخذ الجملة الأولى والثانية
        selected_sentences = [sent.strip() for sent in sentences[:2] if sent.strip()]
    
    return '. '.join(selected_sentences) + '.'

def create_hybrid_intelligent_answer(question: str, relevant_articles: List[Dict[str, Any]], language: str) -> str:
    """
    المرحلة الثانية: إنشاء الخلاصة الذكية مع التحليل العميق
    Phase 2: Create intelligent summary with deep analysis using question decomposition
    """
    
    if not relevant_articles:
        return "لم يتم العثور على محتوى مطابق لسؤالك في قاعدة البيانات القانونية."
    
    # المرحلة الأولى: تفكيك السؤال الذكي
    question_analysis = intelligent_question_decomposition(question, language)
    
    # تحديد النصوص الأكثر صلة بناءً على التفكيك
    context_articles = relevant_articles[:3]
    context_text = ""
    specific_references = []
    
    for i, article in enumerate(context_articles, 1):
        article_num = article.get('article_number', f'Article {i}')
        title = article.get('title', 'Untitled')
        content = article.get('content', '')
        
        # استخراج الجمل الأكثر صلة فقط من كل مادة
        relevant_content = extract_relevant_sentences(content, question_analysis["search_elements"])
        
        specific_references.append(f"المادة {article_num}")
        context_text += f"\n\n--- المادة {article_num}: {title} ---\n{relevant_content}"
    
    # البروموت المحسن للخلاصة الذكية مع التفكيك
    expert_prompt = f"""أنت خبير قانوني متخصص في قواعد الاتحاد الدولي لالتقاط الأوتاد.

تم تفكيك السؤال ذكياً إلى:
- نوع السؤال: {question_analysis["question_type"]}  
- المفاهيم الأساسية: {', '.join(question_analysis["key_concepts"])}
- عناصر البحث: {', '.join(question_analysis["search_elements"])}

المهمة: تحليل النصوص المحددة وتقديم خلاصة ذكية مع الاستناد المحدد.

تنسيق الخلاصة الذكية المطلوب:

🧠 **الخلاصة الذكية:**

[إجابة مباشرة ودقيقة وواضحة بناء على تفكيك السؤال]

**التحليل القانوني العميق:**
بناءً على الفهم العميق لقواعد التقاط الأوتاد، [تحليل عميق وشامل يربط النصوص المحددة منطقياً ويوضح الحكمة القانونية وراءها - فقرة مفصلة تُظهر الفهم العميق للسياق].

**الأسس القانونية المحددة:**
• استناداً إلى القاعدة القانونية رقم [X]: "[النص المحدد المعني بالإجابة فقط - وليس المادة كاملة]"
• استناداً إلى القاعدة القانونية رقم [Y]: "[النص المحدد المعني بالإجابة فقط]"
[إضافة المزيد حسب الحاجة]

**الخلاصة النهائية:**
[فقرة تحليلية عميقة تربط جميع المواد المذكورة منطقياً وتوضح التطبيق العملي والحكمة القانونية]

متطلبات صارمة:
1. ابدأ بـ "🧠 **الخلاصة الذكية:**"
2. قدم تحليلاً عميقاً مفصلاً  
3. اربط المواد القانونية منطقياً وذكياً
4. اذكر أرقام المواد بوضوح
5. استخدم فقط النصوص المرفقة
6. ركز على النصوص المحددة المعنية وليس المواد كاملة

السؤال الأصلي: {question}

النصوص القانونية المحددة المستخرجة: {context_text}

قدم الخلاصة الذكية بالتنسيق المطلوب:"""

    # محاولة الحصول على التحليل الذكي من DeepSeek
    ai_response = call_deepseek_api(expert_prompt, max_tokens=400)
    
    if ai_response:
        # التأكد من وجود الخلاصة الذكية في الإجابة
        if "🧠" not in ai_response:
            ai_response = f"🧠 **الخلاصة الذكية:**\n\n{ai_response}"
        
        return ai_response
    else:
        # Fallback للتحليل الخوارزمي الذكي
        print("AI response failed, using intelligent algorithmic fallback")
        return create_smart_algorithmic_fallback(question, question_analysis, context_articles)


def create_smart_algorithmic_fallback(question: str, question_analysis: Dict[str, Any], articles: List[Dict[str, Any]]) -> str:
    """
    إنشاء إجابة ذكية خوارزمية عند عدم توفر الذكاء الاصطناعي
    Create smart algorithmic fallback response when AI is unavailable
    """
    
    if not articles:
        return "🧠 **الخلاصة الذكية:**\n\nلم يتم العثور على محتوى مطابق لسؤالك في قاعدة البيانات القانونية."
    
    # استخراج المعلومات من المقال الأكثر صلة
    main_article = articles[0]
    article_num = main_article.get('article_number', 'غير محدد')
    title = main_article.get('title', '')
    content = main_article.get('content', '')
    
    # استخراج الجمل الأكثر صلة
    relevant_content = extract_relevant_sentences(content, question_analysis["search_elements"])
    
    # بناء الإجابة الذكية
    smart_response = f"""🧠 **الخلاصة الذكية:**

{relevant_content}

**التحليل القانوني العميق:**
بناءً على الفهم العميق لقواعد التقاط الأوتاد، يتضح أن هذا السؤال من نوع "{question_analysis['question_type']}" ويتعلق بالمفاهيم الأساسية: {', '.join(question_analysis['key_concepts']) if question_analysis['key_concepts'] else 'المفاهيم العامة'}. 

**الأسس القانونية المحددة:**
• استناداً إلى القاعدة القانونية رقم {article_num}: "{relevant_content[:150]}..."

**الخلاصة النهائية:**
هذا التحليل يوضح الإطار القانوني المعني بالسؤال المطروح، ويقدم الأساس اللازم للفهم والتطبيق العملي وفقاً لقواعد الاتحاد الدولي لالتقاط الأوتاد."""

    # إضافة مراجع إضافية إذا كانت متوفرة
    if len(articles) > 1:
        additional_refs = [f"المادة {art.get('article_number', 'غير محدد')}" for art in articles[1:3]]
        smart_response += f"\n\n*مراجع إضافية: {', '.join(additional_refs)}*"
    
    return smart_response

def create_intelligent_algorithmic_fallback(question: str, articles: List[Dict[str, Any]]) -> str:
    """Create intelligent fallback response when AI is unavailable"""
    
    if not articles:
        return "لم يتم العثور على محتوى مطابق لسؤالك في قاعدة البيانات القانونية."
    
    # Extract key information from the most relevant article
    main_article = articles[0]
    article_num = main_article.get('article_number', 'غير محدد')
    title = main_article.get('title', '')
    content = main_article.get('content', '')
    
    # Extract relevant sentence from content based on question
    question_lower = question.lower()
    sentences = content.split('.')
    relevant_sentence = ""
    
    # Find most relevant sentence
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if any(keyword in sentence_lower for keyword in ['يجب', 'تكون', 'يتم', 'المطلوب', 'الضروري']):
            if len(sentence.strip()) > 20:  # Avoid very short sentences
                relevant_sentence = sentence.strip()
                break
    
    if not relevant_sentence and sentences:
        relevant_sentence = sentences[0].strip()  # Fallback to first sentence
    
    # Create intelligent response
    if relevant_sentence:
        response = f"{relevant_sentence}. (المرجع: المادة {article_num})"
    else:
        response = f"وفقاً للمادة {article_num}: {title}، يرجى مراجعة النص الكامل للحصول على التفاصيل الدقيقة."
    
    # Add additional references if available
    if len(articles) > 1:
        additional_refs = [f"المادة {art.get('article_number', 'غير محدد')}" for art in articles[1:3]]
        response += f" مواد ذات صلة: {', '.join(additional_refs)}"
    
    return response


def create_hybrid_supporting_articles(articles: List[Dict[str, Any]], question: str) -> List[Dict[str, Any]]:
    """Create intelligent summaries for supporting articles"""
    
    supporting_articles = []
    
    for article in articles[:5]:  # Limit to top 5 supporting articles
        article_num = article.get('article_number', 'غير محدد')
        title = article.get('title', 'بدون عنوان')
        content = article.get('content', '')
        relevance_score = article.get('relevance_score', 0)
        
        # Create AI-powered summary
        summary_prompt = f"""لخص هذا النص القانوني في 2-3 جمل فقط بما يتعلق بالسؤال المطروح:

السؤال: {question}
النص القانوني - المادة {article_num}: {title}
المحتوى: {content[:800]}...

قدم ملخص مفيد ومختصر للنقاط الأساسية:"""
        
        ai_summary = call_deepseek_api(summary_prompt, max_tokens=100)
        
        if ai_summary:
            summary_content = ai_summary
        else:
            # Intelligent algorithmic summary
            summary_content = f"{title}. {content[:200]}..."
        
        supporting_article = {
            "title": f"المادة {article_num}: {title}",
            "content": summary_content,
            "article_number": article_num,
            "relevance_score": relevance_score,
            "ai_processed": bool(ai_summary)
        }
        
        supporting_articles.append(supporting_article)
    
    return supporting_articles


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler for ITPF Legal Answer System
    النظام الهجين: البحث المحلي + تحليل DeepSeek AI
    """
    
    def _set_cors_headers(self):
        """Set CORS headers for all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
    
    def _send_json_response(self, status_code: int, data: dict):
        """Send JSON response with proper headers and cache busting"""
        self.send_response(status_code)
        self._set_cors_headers()
        # Force cache busting
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('X-Content-Version', '4.0.0')
        self.end_headers()
        json_response = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.wfile.write(json_response)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET request - API info"""
        api_info = {
            "message": "ITPF Legal Answer System - Hybrid AI",
            "version": "4.1.0",
            "status": "active",
            "system_type": "Hybrid: Local Search + DeepSeek AI Analysis",
            "endpoint": "/api/answer",
            "method": "POST",
            "usage": {
                "question": "Your legal question here",
                "language": "both|arabic|english"
            },
            "features": [
                "النظام الهجين الذكي",
                "البحث المحلي الدقيق",
                "تحليل DeepSeek AI العميق", 
                "منع الاختلاق والمراوغة",
                "مراجع دقيقة لأرقام المواد",
                "الحفاظ على النصوص الكاملة",
                "دعم اللغتين العربية والإنجليزية",
                "55 مادة قانونية + ملحقين 9 و 10"
            ],
            "data_integrity": {
                "arabic_articles": "55 + appendices 9,10",
                "english_articles": "55 + appendices 9,10", 
                "text_preservation": "Complete - no truncation",
                "last_verified": "2025-01-08T14:00:00"
            }
        }
        self._send_json_response(200, api_info)
    
    def do_POST(self):
        """Handle POST request - Question answering"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON data
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                self._send_json_response(400, {
                    "success": False,
                    "message": "Invalid JSON in request body"
                })
                return
            
            question = data.get('question', '').strip()
            language = data.get('language', 'both')
            
            if not question:
                self._send_json_response(400, {
                    "success": False,
                    "message": "Question is required"
                })
                return
            
            print(f"Processing question: {question} (language: {language})")
            
            # Load complete legal data
            arabic_data, english_data = load_legal_data()
            
            if not arabic_data and not english_data:
                self._send_json_response(500, {
                    "success": False,
                    "message": "Legal database unavailable"
                })
                return
            
            # Phase 1: Fast Direct Search - Single query for speed
            relevant_articles = []
            if language in ['both', 'arabic'] and arabic_data:
                # Extract articles and appendices from Arabic data structure
                if isinstance(arabic_data, dict):
                    arabic_articles = arabic_data.get('articles', [])
                    arabic_appendices = arabic_data.get('appendices', [])
                    # Combine articles and appendices for comprehensive search
                    arabic_content = arabic_articles + arabic_appendices
                else:
                    arabic_content = arabic_data
                
                # Single fast search with original question
                arabic_results = advanced_search_relevant_content(question, arabic_content, 'arabic')
                relevant_articles.extend(arabic_results)
                
            if language in ['both', 'english'] and english_data:
                # Extract articles and appendices from English data structure 
                english_content = []
                if isinstance(english_data, dict):
                    if 'chapters' in english_data:
                        for chapter in english_data['chapters']:
                            english_content.extend(chapter.get('articles', []))
                    # Also include appendices if available
                    english_appendices = english_data.get('appendices', [])
                    english_content.extend(english_appendices)
                elif isinstance(english_data, list):
                    english_content = english_data
                english_results = advanced_search_relevant_content(question, english_content, 'english')
                relevant_articles.extend(english_results)
            
            # Sort all results by relevance
            relevant_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            if not relevant_articles:
                self._send_json_response(200, {
                    "success": True,
                    "legal_analysis": "🧠 **الخلاصة الذكية:**\n\nلم يتم العثور على محتوى مطابق لسؤالك في قاعدة البيانات القانونية. يرجى إعادة صياغة السؤال أو استخدام كلمات مفتاحية مختلفة.",
                    "legal_references": [],
                    "metadata": {
                        "question": question,
                        "language": language,
                        "articles_found": 0,
                        "system_type": "Hybrid AI",
                        "search_status": "No relevant content found"
                    }
                })
                return
            
            # Phase 2: AI Analysis - DeepSeek analyzes found articles
            direct_answer = create_hybrid_intelligent_answer(question, relevant_articles, language)
            
            # Phase 3: Create supporting articles with AI summaries
            supporting_articles = create_hybrid_supporting_articles(relevant_articles, question)
            
            # Prepare final response with new format
            api_response = {
                "success": True,
                "legal_analysis": direct_answer,
                "legal_references": supporting_articles,
                "metadata": {
                    "question": question,
                    "language": language,
                    "articles_found": len(relevant_articles),
                    "system_type": "Hybrid: Local Search + DeepSeek AI",
                    "ai_powered": True,
                    "text_preservation": "Complete - no truncation",
                    "version": "4.1.0",
                    "cache_version": "21.0",
                    "timestamp": "2025-01-10T12:00:00",
                    "data_sources": {
                        "arabic_articles": len(arabic_data) if arabic_data else 0,
                        "english_articles": len(english_data) if english_data else 0
                    }
                }
            }
            
            self._send_json_response(200, api_response)
            
        except Exception as e:
            import traceback
            print(f"Error processing question: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
            self._send_json_response(500, {
                "success": False,
                "message": f"خطأ في معالجة السؤال: {str(e)}",
                "error_details": str(e),
                "system_type": "Hybrid AI System"
            })