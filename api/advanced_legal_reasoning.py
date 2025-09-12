"""
ITPF Advanced Legal Reasoning System
نظام التفكير القانوني المتقدم - مبني على أحدث تقنيات 2025

يحاكي طريقة تفكير الخبراء القانونيين في ربط النصوص والاستنتاج
"""

import json
import re
from typing import Dict, Any, List, Tuple, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import asyncio
from datetime import datetime


@dataclass
class LegalEntity:
    """كيان قانوني مستخرج من النص"""
    text: str
    entity_type: str  # time, penalty, procedure, exception
    value: Optional[str] = None
    context: str = ""
    article_refs: List[int] = None


@dataclass
class CrossReference:
    """مرجع متقاطع بين المواد القانونية"""
    source_article: int
    target_article: int
    relationship_type: str  # defines, modifies, excepts, requires
    strength: float
    context: str


@dataclass  
class ReasoningStep:
    """خطوة في التفكير المنطقي"""
    step_number: int
    reasoning: str
    evidence: str
    article_refs: List[int]
    confidence: float


class AdvancedLegalReasoning:
    """نظام التفكير القانوني المتقدم"""
    
    def __init__(self):
        self.knowledge_graph = defaultdict(list)
        self.legal_entities = {}
        self.cross_references = []
        self.semantic_clusters = {}
        
        # مؤشرات العلاقات القانونية
        self.relationship_patterns = {
            'defines': [
                r'يُعرف.*?بأنه', r'يُقصد بـ', r'مصطلح.*?يشير إلى',
                r'defined as', r'means', r'refers to'
            ],
            'modifies': [
                r'باستثناء', r'إلا أن', r'ولكن', r'غير أن',
                r'except', r'unless', r'however', r'but'
            ],
            'requires': [
                r'يجب', r'يتوجب', r'يُشترط', r'لا بد من',
                r'must', r'shall', r'required', r'mandatory'
            ],
            'excepts': [
                r'في حالة', r'إذا كان', r'عند حدوث', r'استثناء',
                r'in case of', r'if', r'when', r'exception'
            ]
        }
        
        # كيانات قانونية مهمة
        self.entity_patterns = {
            'time': [
                r'(\d+)\s*(?:ثانية|دقيقة|ساعة|يوم)',
                r'(\d+)\s*(?:second|minute|hour|day)s?'
            ],
            'penalty': [
                r'صفر\s*نقاط?', r'استبعاد', r'خصم', r'عقوبة',
                r'zero\s*points?', r'disqualification', r'penalty'
            ],
            'score': [
                r'(\d+)\s*نقاط?', r'(\d+)\s*points?'
            ]
        }

    def build_knowledge_graph(self, legal_data: Dict[str, Any]) -> None:
        """بناء خريطة المعرفة القانونية"""
        print("🧠 Building advanced knowledge graph...")
        
        all_articles = legal_data.get('articles', []) + legal_data.get('appendices', [])
        
        for article in all_articles:
            article_num = article.get('article_number', 'appendix')
            content = article.get('content', '')
            
            # استخراج الكيانات القانونية
            entities = self._extract_legal_entities(content, article_num)
            self.legal_entities[article_num] = entities
            
            # بناء المراجع المتقاطعة
            cross_refs = self._find_cross_references(article, all_articles)
            self.cross_references.extend(cross_refs)
            
            # تجميع دلالي للمواد المترابطة
            self._build_semantic_clusters(article, all_articles)

    def _extract_legal_entities(self, content: str, article_num) -> List[LegalEntity]:
        """استخراج الكيانات القانونية من النص"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity = LegalEntity(
                        text=match.group(0),
                        entity_type=entity_type,
                        value=match.group(1) if match.groups() else match.group(0),
                        context=content[max(0, match.start()-50):match.end()+50],
                        article_refs=[article_num]
                    )
                    entities.append(entity)
        
        return entities

    def _find_cross_references(self, article: Dict, all_articles: List[Dict]) -> List[CrossReference]:
        """العثور على المراجع المتقاطعة بين المواد"""
        cross_refs = []
        source_num = article.get('article_number', 'appendix')
        content = article.get('content', '').lower()
        
        for rel_type, patterns in self.relationship_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    # البحث عن المواد المرتبطة
                    for other_article in all_articles:
                        target_num = other_article.get('article_number', 'appendix')
                        if target_num != source_num:
                            # حساب قوة العلاقة بناء على التشابه الدلالي
                            strength = self._calculate_semantic_similarity(
                                content, other_article.get('content', '').lower()
                            )
                            
                            if strength > 0.3:  # عتبة العلاقة
                                cross_ref = CrossReference(
                                    source_article=source_num,
                                    target_article=target_num,
                                    relationship_type=rel_type,
                                    strength=strength,
                                    context=content[:200]
                                )
                                cross_refs.append(cross_ref)
        
        return cross_refs

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه الدلالي بين النصوص"""
        # خوارزمية مبسطة للتشابه الدلالي
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        # مصطلحات قانونية مهمة لها وزن أكبر
        legal_terms = {
            'متسابق', 'نقاط', 'وقت', 'استبعاد', 'عقوبة', 'ثانية', 'دقيقة',
            'contestant', 'points', 'time', 'disqualification', 'penalty', 'seconds'
        }
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        # زيادة الوزن للمصطلحات القانونية
        weighted_intersection = len(intersection)
        for term in intersection:
            if term in legal_terms:
                weighted_intersection += 0.5
        
        return weighted_intersection / len(union)

    def _build_semantic_clusters(self, article: Dict, all_articles: List[Dict]) -> None:
        """بناء التجميعات الدلالية للمواد"""
        # تجميع المواد حسب الموضوع (التوقيت، النقاط، العقوبات...)
        content = article.get('content', '').lower()
        article_num = article.get('article_number', 'appendix')
        
        clusters = {
            'timing': ['وقت', 'ثانية', 'دقيقة', 'مهلة', 'time', 'second', 'minute'],
            'scoring': ['نقاط', 'درجة', 'تسجيل', 'points', 'score', 'scoring'],
            'penalties': ['عقوبة', 'استبعاد', 'خصم', 'penalty', 'disqualification'],
            'exceptions': ['استثناء', 'إلا', 'باستثناء', 'exception', 'except', 'unless']
        }
        
        for cluster_name, keywords in clusters.items():
            if any(keyword in content for keyword in keywords):
                if cluster_name not in self.semantic_clusters:
                    self.semantic_clusters[cluster_name] = []
                self.semantic_clusters[cluster_name].append(article_num)

    def perform_multi_hop_reasoning(self, question: str, context: List[Dict]) -> List[ReasoningStep]:
        """التفكير المتعدد المراحل لربط المواد"""
        reasoning_steps = []
        
        # تحليل السؤال لاستخراج الكيانات المهمة
        question_entities = self._extract_question_entities(question)
        
        # الخطوة 1: العثور على المواد ذات الصلة المباشرة
        direct_articles = self._find_direct_relevant_articles(question_entities, context)
        
        if direct_articles:
            step1 = ReasoningStep(
                step_number=1,
                reasoning=f"تم العثور على {len(direct_articles)} مادة ذات صلة مباشرة بالسؤال",
                evidence=f"المواد: {[art.get('article_number') for art in direct_articles]}",
                article_refs=[art.get('article_number') for art in direct_articles],
                confidence=0.9
            )
            reasoning_steps.append(step1)
        
        # الخطوة 2: البحث عن المواد المترابطة عبر المراجع المتقاطعة
        linked_articles = self._find_cross_referenced_articles(direct_articles, context)
        
        if linked_articles:
            step2 = ReasoningStep(
                step_number=2,
                reasoning="العثور على مواد مترابطة تحتوي على قوانين أساسية أو استثناءات",
                evidence=f"المواد المترابطة: {[art.get('article_number') for art in linked_articles]}",
                article_refs=[art.get('article_number') for art in linked_articles],
                confidence=0.8
            )
            reasoning_steps.append(step2)
        
        # الخطوة 3: تحليل العلاقات والاستثناءات
        exceptions_and_rules = self._analyze_rules_and_exceptions(
            direct_articles + linked_articles, question_entities
        )
        
        if exceptions_and_rules:
            step3 = ReasoningStep(
                step_number=3,
                reasoning="تحليل القوانين الأساسية والاستثناءات المطبقة",
                evidence=exceptions_and_rules['analysis'],
                article_refs=exceptions_and_rules['article_refs'],
                confidence=0.95
            )
            reasoning_steps.append(step3)
        
        return reasoning_steps

    def _extract_question_entities(self, question: str) -> List[str]:
        """استخراج الكيانات المهمة من السؤال"""
        entities = []
        
        # استخراج الأرقام (قد تكون أوقات أو نقاط)
        numbers = re.findall(r'\d+', question)
        entities.extend(numbers)
        
        # استخراج الكلمات المفتاحية القانونية
        legal_keywords = [
            'تأخر', 'عقوبة', 'استثناء', 'نقاط', 'ثانية', 'استبعاد',
            'delay', 'penalty', 'exception', 'points', 'seconds', 'disqualification'
        ]
        
        for keyword in legal_keywords:
            if keyword in question.lower():
                entities.append(keyword)
        
        return entities

    def _find_direct_relevant_articles(self, entities: List[str], context: List[Dict]) -> List[Dict]:
        """العثور على المواد ذات الصلة المباشرة"""
        relevant_articles = []
        
        for article in context:
            content = article.get('content', '').lower()
            relevance_score = 0
            
            # حساب الصلة بناء على الكيانات المستخرجة
            for entity in entities:
                if entity.lower() in content:
                    relevance_score += 1
                    
                # وزن إضافي للأرقام المطابقة تماماً
                if entity.isdigit() and f"{entity} ثانية" in content:
                    relevance_score += 2
            
            if relevance_score > 0:
                article['computed_relevance'] = relevance_score
                relevant_articles.append(article)
        
        # ترتيب حسب الصلة
        return sorted(relevant_articles, key=lambda x: x.get('computed_relevance', 0), reverse=True)

    def _find_cross_referenced_articles(self, direct_articles: List[Dict], all_context: List[Dict]) -> List[Dict]:
        """العثور على المواد المترابطة عبر المراجع المتقاطعة"""
        linked_articles = []
        
        for article in direct_articles:
            article_num = article.get('article_number')
            
            # البحث عن المراجع المتقاطعة في قاعدة البيانات
            for cross_ref in self.cross_references:
                if cross_ref.source_article == article_num or cross_ref.target_article == article_num:
                    # العثور على المادة المرتبطة في السياق
                    target_num = (cross_ref.target_article if cross_ref.source_article == article_num 
                                 else cross_ref.source_article)
                    
                    for context_article in all_context:
                        if context_article.get('article_number') == target_num:
                            context_article['cross_ref_type'] = cross_ref.relationship_type
                            context_article['cross_ref_strength'] = cross_ref.strength
                            linked_articles.append(context_article)
        
        return linked_articles

    def _analyze_rules_and_exceptions(self, articles: List[Dict], question_entities: List[str]) -> Dict:
        """تحليل القوانين والاستثناءات"""
        analysis = {
            'main_rules': [],
            'exceptions': [],
            'analysis': "",
            'article_refs': []
        }
        
        for article in articles:
            content = article.get('content', '')
            article_num = article.get('article_number')
            
            # تحديد نوع المادة (قانون أساسي أو استثناء)
            if any(word in content.lower() for word in ['استثناء', 'إلا', 'باستثناء', 'exception', 'except']):
                analysis['exceptions'].append({
                    'article': article_num,
                    'content': content[:200] + "..."
                })
            else:
                # البحث عن القوانين الأساسية (العقوبات، القواعد)
                if any(word in content.lower() for word in ['عقوبة', 'استبعاد', 'صفر نقاط', 'penalty', 'disqualification']):
                    analysis['main_rules'].append({
                        'article': article_num,
                        'content': content[:200] + "..."
                    })
            
            analysis['article_refs'].append(article_num)
        
        # تكوين النص التحليلي
        if analysis['main_rules'] and analysis['exceptions']:
            analysis['analysis'] = f"تم العثور على {len(analysis['main_rules'])} قانون أساسي و {len(analysis['exceptions'])} استثناء. "
            analysis['analysis'] += "القوانين الأساسية تحدد العقوبة، والاستثناءات تحدد الحالات التي لا تطبق فيها العقوبة."
        
        return analysis

    def calculate_advanced_relevance(self, article: Dict, question: str, question_entities: List[str]) -> float:
        """حساب الصلة المتقدم بناء على التحليل الدلالي والعلاقات"""
        base_score = 0.0
        content = article.get('content', '').lower()
        
        # النقاط الأساسية للكيانات
        for entity in question_entities:
            if entity.lower() in content:
                base_score += 1.0
                
                # نقاط إضافية للمطابقات الدقيقة
                if entity.isdigit():
                    if f"{entity} ثانية" in content or f"{entity} second" in content:
                        base_score += 3.0
                    elif f"{entity} نقطة" in content or f"{entity} point" in content:
                        base_score += 2.0
        
        # نقاط للمراجع المتقاطعة
        article_num = article.get('article_number')
        for cross_ref in self.cross_references:
            if cross_ref.source_article == article_num or cross_ref.target_article == article_num:
                base_score += cross_ref.strength * 2.0
        
        # نقاط للتجميعات الدلالية
        for cluster_name, cluster_articles in self.semantic_clusters.items():
            if article_num in cluster_articles:
                # تحديد أهمية الكلاسترات بناء على السؤال
                cluster_relevance = {
                    'timing': 3.0 if any(word in question.lower() for word in ['وقت', 'ثانية', 'تأخر', 'time', 'delay']) else 0,
                    'penalties': 4.0 if any(word in question.lower() for word in ['عقوبة', 'استبعاد', 'penalty']) else 0,
                    'exceptions': 3.5 if 'استثناء' in question.lower() or 'exception' in question.lower() else 0,
                    'scoring': 2.0 if 'نقاط' in question.lower() or 'points' in question.lower() else 0
                }
                base_score += cluster_relevance.get(cluster_name, 0.5)
        
        # تطبيع النتيجة إلى نسبة مئوية
        max_possible_score = len(question_entities) * 4.0 + 10.0  # تقدير أقصى نقاط ممكنة
        normalized_score = min(100.0, (base_score / max_possible_score) * 100)
        
        return normalized_score

    def format_structured_response(self, question: str, reasoning_steps: List[ReasoningStep], 
                                 relevant_articles: List[Dict]) -> Dict[str, Any]:
        """تنسيق الإجابة المهيكلة والواضحة"""
        
        # استخراج الخلاصة الذكية من خطوات التفكير
        main_conclusion = self._generate_smart_conclusion(question, reasoning_steps, relevant_articles)
        
        # تنظيم المواد المستندة حسب الأهمية
        legal_references = self._organize_legal_references(relevant_articles)
        
        response = {
            "smart_legal_analysis": main_conclusion,
            "legal_foundation": legal_references,
            "reasoning_quality": {
                "steps_performed": len(reasoning_steps),
                "cross_references_found": len([step for step in reasoning_steps if "مترابطة" in step.reasoning]),
                "confidence_level": sum(step.confidence for step in reasoning_steps) / len(reasoning_steps) if reasoning_steps else 0.5
            }
        }
        
        return response

    def _generate_smart_conclusion(self, question: str, reasoning_steps: List[ReasoningStep], 
                                 articles: List[Dict]) -> str:
        """توليد الخلاصة الذكية بناء على التحليل"""
        if not reasoning_steps:
            return "لم يتم العثور على تحليل كافٍ للسؤال."
        
        # تحليل نوع السؤال لتحديد هيكل الإجابة
        question_type = self._classify_question_type(question)
        
        conclusion = "## التحليل القانوني الذكي\n\n"
        
        if question_type == "penalty_timing":
            # سؤال عن العقوبات والتوقيت
            main_rule = self._extract_main_rule(articles)
            exceptions = self._extract_exceptions(articles)
            
            if main_rule and exceptions:
                conclusion += f"**الحكم القانوني:** {main_rule['rule']}\n\n"
                conclusion += f"**الاستثناءات:** {exceptions['exception']}\n\n"
            elif main_rule:
                conclusion += f"**الحكم القانوني:** {main_rule['rule']}\n\n"
        
        elif question_type == "scoring":
            # سؤال عن النقاط
            scoring_rule = self._extract_scoring_rule(articles)
            if scoring_rule:
                conclusion += f"**نظام النقاط:** {scoring_rule}\n\n"
        
        # إضافة الأساس القانوني
        conclusion += "**استناداً للمواد القانونية التالية:**\n"
        
        return conclusion

    def _classify_question_type(self, question: str) -> str:
        """تصنيف نوع السؤال"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['تأخر', 'ثانية', 'عقوبة', 'delay', 'penalty']):
            return "penalty_timing"
        elif any(word in question_lower for word in ['نقاط', 'نقطة', 'points', 'score']):
            return "scoring"
        elif any(word in question_lower for word in ['استثناء', 'exception']):
            return "exceptions"
        else:
            return "general"

    def _extract_main_rule(self, articles: List[Dict]) -> Optional[Dict]:
        """استخراج القانون الأساسي"""
        for article in articles:
            content = article.get('content', '')
            if any(word in content.lower() for word in ['صفر نقاط', 'استبعاد', 'عقوبة']):
                # استخراج القانون الأساسي
                rule_text = self._extract_key_sentence(content, ['صفر نقاط', 'استبعاد', 'عقوبة'])
                if rule_text:
                    return {
                        'rule': rule_text,
                        'article': article.get('article_number'),
                        'type': 'main_rule'
                    }
        return None

    def _extract_exceptions(self, articles: List[Dict]) -> Optional[Dict]:
        """استخراج الاستثناءات"""
        for article in articles:
            content = article.get('content', '')
            if any(word in content.lower() for word in ['استثناء', 'إلا', 'باستثناء']):
                exception_text = self._extract_key_sentence(content, ['استثناء', 'إلا', 'باستثناء'])
                if exception_text:
                    return {
                        'exception': exception_text,
                        'article': article.get('article_number'),
                        'type': 'exception'
                    }
        return None

    def _extract_key_sentence(self, content: str, keywords: List[str]) -> Optional[str]:
        """استخراج الجملة المفتاحية التي تحتوي على الكلمات المهمة"""
        sentences = content.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                return sentence.strip()
        return None

    def _extract_scoring_rule(self, articles: List[Dict]) -> Optional[str]:
        """استخراج قوانين النقاط"""
        for article in articles:
            content = article.get('content', '')
            if 'نقاط' in content.lower() or 'points' in content.lower():
                # البحث عن الجملة التي تحتوي على النقاط
                scoring_sentence = self._extract_key_sentence(content, ['نقاط', 'نقطة', 'points'])
                return scoring_sentence
        return None

    def _organize_legal_references(self, articles: List[Dict]) -> List[Dict]:
        """تنظيم المراجع القانونية حسب الأهمية"""
        references = []
        
        for article in articles:
            ref = {
                "article_number": article.get('article_number'),
                "title": article.get('title', ''),
                "key_content": article.get('content', '')[:300] + "...",
                "relevance_percentage": round(article.get('computed_relevance', 0) * 10, 1),
                "reference_type": article.get('cross_ref_type', 'direct')
            }
            references.append(ref)
        
        # ترتيب حسب الأهمية
        return sorted(references, key=lambda x: x['relevance_percentage'], reverse=True)


# إنشاء مثيل النظام المتقدم
advanced_reasoning = AdvancedLegalReasoning()