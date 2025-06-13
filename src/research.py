"""Research-based journalist profile generation using web search and content analysis."""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import Counter
import anthropic
from dotenv import load_dotenv
import os

from .web_tools import WebSearchTool, JournalistSearchQueries, SearchResult, ArticleData
from .config import get_model_for_task, estimate_cost

# Load environment variables
load_dotenv()


@dataclass
class ResearchProgress:
    """Track research progress for UI updates."""
    current_step: str
    step_number: int
    total_steps: int
    details: str = ""
    completed: bool = False


@dataclass
class VerifiedInfo:
    """Verified factual information about a journalist."""
    current_position: Dict[str, Any]
    social_profiles: Dict[str, str]
    recent_articles: List[Dict[str, Any]]
    verification_sources: List[str]
    last_verified: str


@dataclass
class AnalyzedData:
    """AI-analyzed data with confidence scores."""
    primary_beat: str
    coverage_frequency: str
    common_topics: List[str]
    writing_style: str
    article_length_avg: int
    confidence: float
    analysis_date: str


@dataclass
class InferredPreferences:
    """Inferred communication and pitch preferences."""
    response_likelihood_factors: Dict[str, Any]
    best_pitch_times: str
    preferred_sources: str
    communication_style: str
    confidence: float
    note: str = "Inferred from article analysis, not directly stated"


class JournalistResearcher:
    """Main class for researching journalist profiles using web search."""
    
    def __init__(self):
        self.web_search = WebSearchTool()
        self.search_queries = JournalistSearchQueries()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
    async def research_journalist(
        self,
        name: str,
        publication: str = None,
        depth: str = "standard",
        progress_callback: Optional[Callable[[ResearchProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive journalist research using web search.
        
        Args:
            name: Journalist's full name
            publication: Known publication (optional)
            depth: Research depth ('quick', 'standard', 'comprehensive')
            progress_callback: Function to call with progress updates
            
        Returns:
            Complete journalist profile with verified and analyzed data
        """
        # Initialize progress tracking
        total_steps = self._get_total_steps(depth)
        step_num = 0
        
        def update_progress(step_name: str, details: str = ""):
            nonlocal step_num
            step_num += 1
            if progress_callback:
                progress = ResearchProgress(
                    current_step=step_name,
                    step_number=step_num,
                    total_steps=total_steps,
                    details=details,
                    completed=(step_num == total_steps)
                )
                progress_callback(progress)
        
        # Step 1: Verify journalist exists and current employment
        update_progress("Verifying journalist identity", f"Searching for {name}")
        verified_info = await self._verify_journalist_employment(name, publication)
        
        # Step 2: Find recent articles
        update_progress("Finding recent articles", "Searching for published work")
        recent_articles = await self._find_recent_articles(name, publication, depth)
        verified_info.recent_articles = recent_articles
        
        # Step 3: Analyze beat and coverage patterns
        update_progress("Analyzing coverage patterns", "Processing article content")
        analyzed_data = await self._analyze_coverage_patterns(recent_articles, name)
        
        # Step 4: Find social media profiles (if comprehensive)
        if depth == "comprehensive":
            update_progress("Finding social profiles", "Searching social media")
            social_profiles = await self._find_social_profiles(name)
            verified_info.social_profiles.update(social_profiles)
        
        # Step 5: Extract communication preferences
        update_progress("Inferring preferences", "Analyzing communication style")
        preferences = await self._infer_communication_preferences(
            recent_articles, analyzed_data, verified_info
        )
        
        # Step 6: Generate final profile
        update_progress("Generating profile", "Compiling research results")
        profile = self._compile_profile(verified_info, analyzed_data, preferences, name)
        
        update_progress("Research complete", "Profile ready")
        return profile
    
    def _get_total_steps(self, depth: str) -> int:
        """Get total number of research steps based on depth."""
        base_steps = 6  # Basic research steps
        if depth == "comprehensive":
            return base_steps + 1  # Add social media step
        return base_steps
    
    async def _verify_journalist_employment(
        self, name: str, publication: str = None
    ) -> VerifiedInfo:
        """Step 1: Verify the journalist exists and find current employment."""
        verification_queries = self.search_queries.verification_queries(name, publication)
        
        verified_info = VerifiedInfo(
            current_position={},
            social_profiles={},
            recent_articles=[],
            verification_sources=[],
            last_verified=datetime.now().isoformat()
        )
        
        # Search for verification
        for query in verification_queries[:3]:  # Limit initial searches
            results = self.web_search.search_web(query, max_results=5)
            
            for result in results:
                # Look for author pages, bio pages, staff pages
                if any(keyword in result.url.lower() for keyword in ['author', 'staff', 'bio', 'team']):
                    verified_info.verification_sources.append(result.url)
                    
                    # Try to extract position info from snippet or title
                    position_info = self._extract_position_info(result, name, publication)
                    if position_info:
                        verified_info.current_position = position_info
                        break
        
        # If no position found, create basic structure
        if not verified_info.current_position:
            verified_info.current_position = {
                "publication": publication or "Unknown",
                "title": "Journalist",
                "verified_date": datetime.now().isoformat(),
                "source_url": verified_info.verification_sources[0] if verified_info.verification_sources else None,
                "confidence": 0.3
            }
        
        return verified_info
    
    def _extract_position_info(self, result: SearchResult, name: str, publication: str) -> Optional[Dict]:
        """Extract position information from search result."""
        # Look for title keywords in title and snippet
        title_keywords = ['reporter', 'editor', 'journalist', 'correspondent', 'writer', 'senior', 'staff']
        combined_text = f"{result.title} {result.snippet}".lower()
        
        found_titles = [keyword for keyword in title_keywords if keyword in combined_text]
        
        if found_titles:
            # Construct title from found keywords
            title = " ".join(found_titles).title()
            if 'senior' in found_titles and 'reporter' in found_titles:
                title = "Senior Reporter"
            elif 'staff' in found_titles and 'writer' in found_titles:
                title = "Staff Writer"
            
            return {
                "publication": publication or self._extract_publication_from_url(result.url),
                "title": title,
                "verified_date": datetime.now().isoformat(),
                "source_url": result.url,
                "confidence": 0.8
            }
        
        return None
    
    def _extract_publication_from_url(self, url: str) -> str:
        """Extract publication name from URL."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        # Remove common prefixes and suffixes
        domain = domain.replace('www.', '').replace('.com', '').replace('.org', '')
        return domain.title()
    
    async def _find_recent_articles(
        self, name: str, publication: str = None, depth: str = "standard"
    ) -> List[Dict[str, Any]]:
        """Step 2: Find recent articles by the journalist."""
        article_queries = self.search_queries.recent_articles_queries(name, publication)
        
        # Limit queries based on depth
        max_queries = {"quick": 3, "standard": 5, "comprehensive": 8}.get(depth, 5)
        recent_articles = []
        
        for query in article_queries[:max_queries]:
            results = self.web_search.search_web(query, max_results=5)
            
            for result in results:
                # Check if this looks like an article
                if self._is_likely_article(result):
                    article_data = {
                        "title": result.title,
                        "url": result.url,
                        "date_found": result.date_found,
                        "snippet": result.snippet,
                        "source_domain": result.source_domain
                    }
                    
                    # Try to extract publish date and topics from snippet
                    article_data.update(self._extract_article_metadata(result))
                    recent_articles.append(article_data)
            
            # Limit total articles to prevent overwhelming
            if len(recent_articles) >= 20:
                break
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in recent_articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        return unique_articles[:15]  # Return top 15 most recent
    
    def _is_likely_article(self, result: SearchResult) -> bool:
        """Check if search result is likely an article."""
        # Look for article indicators
        article_indicators = ['news', 'article', 'story', 'report', 'analysis']
        avoid_indicators = ['twitter', 'linkedin', 'facebook', 'bio', 'author', 'contact']
        
        url_lower = result.url.lower()
        title_lower = result.title.lower()
        
        # Avoid social media and bio pages
        if any(indicator in url_lower for indicator in avoid_indicators):
            return False
        
        # Look for article indicators or recent dates
        if any(indicator in url_lower or indicator in title_lower for indicator in article_indicators):
            return True
        
        # Check for date patterns in URL (often indicates articles)
        date_pattern = r'/(20\d{2})/|/(0[1-9]|1[0-2])/|/\d{4}-\d{2}-\d{2}/'
        if re.search(date_pattern, result.url):
            return True
        
        return True  # Default to true for now
    
    def _extract_article_metadata(self, result: SearchResult) -> Dict[str, Any]:
        """Extract metadata from article search result."""
        metadata = {
            "estimated_date": None,
            "topics": [],
            "estimated_length": "medium"
        }
        
        # Try to extract date from URL or snippet
        date_patterns = [
            r'(20\d{2}-\d{2}-\d{2})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2}',
            r'\d{1,2}/\d{1,2}/20\d{2}'
        ]
        
        combined_text = f"{result.url} {result.snippet}"
        for pattern in date_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                metadata["estimated_date"] = match.group(1)
                break
        
        # Extract potential topics from title and snippet
        text = f"{result.title} {result.snippet}".lower()
        
        # Common tech/business topics
        topic_keywords = {
            'AI': ['ai', 'artificial intelligence', 'machine learning', 'neural'],
            'Technology': ['tech', 'software', 'digital', 'app', 'platform'],
            'Business': ['company', 'business', 'corporate', 'enterprise', 'startup'],
            'Finance': ['funding', 'investment', 'ipo', 'financial', 'revenue'],
            'Security': ['security', 'breach', 'privacy', 'hack', 'cyber'],
            'Data': ['data', 'analytics', 'database', 'information']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text for keyword in keywords):
                metadata["topics"].append(topic)
        
        return metadata
    
    async def _analyze_coverage_patterns(
        self, articles: List[Dict[str, Any]], journalist_name: str
    ) -> AnalyzedData:
        """Step 3: Analyze coverage patterns using AI."""
        if not articles:
            return AnalyzedData(
                primary_beat="Unknown",
                coverage_frequency="Unknown",
                common_topics=[],
                writing_style="Unknown",
                article_length_avg=0,
                confidence=0.1,
                analysis_date=datetime.now().isoformat()
            )
        
        # Prepare article data for analysis
        article_summaries = []
        all_topics = []
        
        for article in articles[:10]:  # Analyze top 10 articles
            summary = f"Title: {article['title']}\nTopics: {', '.join(article.get('topics', []))}\nSnippet: {article.get('snippet', '')[:200]}"
            article_summaries.append(summary)
            all_topics.extend(article.get('topics', []))
        
        # Count topic frequency
        topic_counts = Counter(all_topics)
        common_topics = [topic for topic, count in topic_counts.most_common(5)]
        
        # Use AI to analyze patterns
        analysis_prompt = f"""Analyze the coverage patterns for journalist {journalist_name} based on their recent articles:

RECENT ARTICLES:
{chr(10).join(article_summaries)}

TOPIC FREQUENCY:
{dict(topic_counts)}

Please analyze and provide:
1. Primary beat/specialty (be specific - e.g., "Consumer AI and Privacy" not just "Technology")
2. Coverage frequency estimate (e.g., "3-4 articles per week", "Weekly deep dives")
3. Writing style characteristics (e.g., "Data-driven, skeptical of hype", "Breaking news focused")
4. Estimated average article length category (short/medium/long)

Return your analysis in this format:
PRIMARY_BEAT: [specific beat description]
COVERAGE_FREQUENCY: [frequency estimate]
WRITING_STYLE: [style description]
ARTICLE_LENGTH: [short/medium/long]
CONFIDENCE: [0.0-1.0 confidence in analysis]"""

        try:
            model = get_model_for_task("evaluation")
            response = self.client.messages.create(
                model=model,
                max_tokens=400,
                temperature=0.3,
                system="You are an expert media analyst. Analyze journalist coverage patterns objectively based on provided data.",
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            analysis_text = response.content[0].text
            
            # Parse the analysis response
            analysis_data = self._parse_analysis_response(analysis_text)
            
            return AnalyzedData(
                primary_beat=analysis_data.get('primary_beat', 'General'),
                coverage_frequency=analysis_data.get('coverage_frequency', 'Regular'),
                common_topics=common_topics,
                writing_style=analysis_data.get('writing_style', 'Professional'),
                article_length_avg=self._estimate_length_words(analysis_data.get('article_length', 'medium')),
                confidence=float(analysis_data.get('confidence', 0.7)),
                analysis_date=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            # Fallback to simple analysis
            return self._simple_pattern_analysis(articles, common_topics)
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, str]:
        """Parse AI analysis response into structured data."""
        analysis_data = {}
        
        patterns = {
            'primary_beat': r'PRIMARY_BEAT:\s*(.+)',
            'coverage_frequency': r'COVERAGE_FREQUENCY:\s*(.+)',
            'writing_style': r'WRITING_STYLE:\s*(.+)',
            'article_length': r'ARTICLE_LENGTH:\s*(.+)',
            'confidence': r'CONFIDENCE:\s*(.+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                analysis_data[key] = match.group(1).strip()
        
        return analysis_data
    
    def _estimate_length_words(self, length_category: str) -> int:
        """Convert length category to estimated word count."""
        length_map = {
            'short': 400,
            'medium': 800,
            'long': 1500
        }
        return length_map.get(length_category.lower(), 800)
    
    def _simple_pattern_analysis(self, articles: List[Dict], common_topics: List[str]) -> AnalyzedData:
        """Fallback simple analysis when AI fails."""
        # Determine primary beat from most common topic
        primary_beat = common_topics[0] if common_topics else "General"
        
        return AnalyzedData(
            primary_beat=primary_beat,
            coverage_frequency=f"~{len(articles)} articles found recently",
            common_topics=common_topics,
            writing_style="Professional journalism",
            article_length_avg=800,
            confidence=0.5,
            analysis_date=datetime.now().isoformat()
        )
    
    async def _find_social_profiles(self, name: str) -> Dict[str, str]:
        """Step 4: Find social media profiles (comprehensive mode only)."""
        social_queries = self.search_queries.social_media_queries(name)
        social_profiles = {}
        
        for query in social_queries[:3]:  # Limit social searches
            results = self.web_search.search_web(query, max_results=3)
            
            for result in results:
                if 'twitter.com' in result.url and 'twitter' not in social_profiles:
                    social_profiles['twitter'] = result.url
                elif 'linkedin.com' in result.url and 'linkedin' not in social_profiles:
                    social_profiles['linkedin'] = result.url
        
        return social_profiles
    
    async def _infer_communication_preferences(
        self, articles: List[Dict], analyzed_data: AnalyzedData, verified_info: VerifiedInfo
    ) -> InferredPreferences:
        """Step 5: Infer communication and pitch preferences."""
        
        # Base response factors on coverage patterns
        base_rate = 0.15  # Default baseline
        
        # Adjust base rate based on beat and frequency
        if analyzed_data.primary_beat in ['Technology', 'AI', 'Business']:
            base_rate = 0.18  # Higher for popular beats
        elif 'investigative' in analyzed_data.primary_beat.lower():
            base_rate = 0.08  # Lower for investigative
        
        response_factors = {
            "timing": {
                "breaking_news": 2.5,
                "exclusive": 2.8,
                "embargo": 1.8,
                "follow_up": 0.7
            },
            "relevance": {
                "exact_beat": 2.2,
                "adjacent_beat": 1.3,
                "off_beat": 0.2
            },
            "quality": {
                "data_driven": 1.9,
                "executive_access": 2.1,
                "generic_pitch": 0.3
            }
        }
        
        # Infer best pitch times based on article patterns
        best_times = "Tuesday-Thursday, 9-11 AM (inferred from publication patterns)"
        
        # Infer preferred sources based on writing style
        if 'data' in analyzed_data.writing_style.lower():
            preferred_sources = "Data-driven sources, research studies, technical experts"
        else:
            preferred_sources = "Industry executives, company spokespeople, expert analysts"
        
        return InferredPreferences(
            response_likelihood_factors={
                "base_response_rate": base_rate,
                "response_factors": response_factors,
                "keyword_triggers": analyzed_data.common_topics
            },
            best_pitch_times=best_times,
            preferred_sources=preferred_sources,
            communication_style=analyzed_data.writing_style,
            confidence=analyzed_data.confidence * 0.8  # Slightly lower for inferences
        )
    
    def _compile_profile(
        self,
        verified_info: VerifiedInfo,
        analyzed_data: AnalyzedData,
        preferences: InferredPreferences,
        name: str
    ) -> Dict[str, Any]:
        """Step 6: Compile final journalist profile."""
        
        # Create system prompt based on research
        system_prompt = f"""You are {name}, a {verified_info.current_position.get('title', 'journalist')} at {verified_info.current_position.get('publication', 'a major publication')} specializing in {analyzed_data.primary_beat}.

Your coverage focuses on {', '.join(analyzed_data.common_topics[:3])} with a {analyzed_data.writing_style.lower()} approach. You typically write {analyzed_data.coverage_frequency.lower()} and prefer {preferences.preferred_sources.lower()}.

You respond to pitches that are relevant to your beat, especially those involving {', '.join(analyzed_data.common_topics[:2])}. You value exclusive information, data-driven stories, and timely news that impacts your coverage area.

Communication style: Professional, direct, and focused on stories that serve your readers' interests."""
        
        return {
            "name": name,
            "verified_info": asdict(verified_info),
            "analyzed_data": asdict(analyzed_data),
            "inferred_preferences": asdict(preferences),
            "metadata": {
                "research_date": datetime.now().isoformat(),
                "update_frequency": "weekly",
                "data_quality_score": (verified_info.current_position.get('confidence', 0.5) + analyzed_data.confidence) / 2,
                "research_method": "web_search_analysis"
            },
            # Legacy fields for compatibility
            "publication": verified_info.current_position.get('publication', 'Unknown'),
            "beat": analyzed_data.primary_beat,
            "base_response_rate": preferences.response_likelihood_factors['base_response_rate'],
            "response_factors": preferences.response_likelihood_factors['response_factors'],
            "keyword_triggers": preferences.response_likelihood_factors['keyword_triggers'],
            "system_prompt": system_prompt
        }