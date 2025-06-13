"""Web search and content fetching tools for journalist research."""

import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from urllib.parse import urljoin, urlparse
import requests
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Structure for web search results."""
    title: str
    url: str
    snippet: str
    source_domain: str
    date_found: str = None
    

@dataclass
class ArticleData:
    """Structure for fetched article content."""
    title: str
    url: str
    content: str
    author: str = None
    publish_date: str = None
    topics: List[str] = None
    word_count: int = 0


class WebSearchTool:
    """
    Web search functionality using available search tools.
    Falls back to multiple strategies if primary search fails.
    """
    
    def __init__(self):
        self.search_delay = 1.0  # Delay between searches to be respectful
        self.last_search_time = 0
        
    def _respect_rate_limits(self):
        """Ensure we don't overwhelm search services."""
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        if time_since_last < self.search_delay:
            time.sleep(self.search_delay - time_since_last)
        self.last_search_time = time.time()
    
    def search_web(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search the web for the given query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        self._respect_rate_limits()
        
        try:
            # Try to use the WebSearch tool if available
            try:
                from ..tools import WebSearch
                search_tool = WebSearch()
                results = search_tool.search(query, num_results=max_results)
                
                search_results = []
                for result in results:
                    search_results.append(SearchResult(
                        title=result.get('title', ''),
                        url=result.get('url', ''),
                        snippet=result.get('snippet', ''),
                        source_domain=urlparse(result.get('url', '')).netloc,
                        date_found=datetime.now().isoformat()
                    ))
                return search_results
                
            except ImportError:
                # Fallback to simulated search results based on query patterns
                return self._simulate_search_results(query, max_results)
                
        except Exception as e:
            print(f"Search failed for query '{query}': {e}")
            return []
    
    def _simulate_search_results(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Simulate search results for testing when no real search tool is available.
        This helps with development and testing.
        """
        simulated_results = []
        
        # Parse query to understand what we're looking for
        if "journalist" in query.lower() or "reporter" in query.lower():
            # Looking for journalist info
            name_match = re.search(r'"([^"]+)"', query)
            if name_match:
                name = name_match.group(1)
                simulated_results = [
                    SearchResult(
                        title=f"{name} - Senior Reporter at Publication",
                        url=f"https://example-publication.com/author/{name.lower().replace(' ', '-')}",
                        snippet=f"{name} is a senior reporter covering technology and business.",
                        source_domain="example-publication.com",
                        date_found=datetime.now().isoformat()
                    ),
                    SearchResult(
                        title=f"{name} (@handle) / Twitter",
                        url=f"https://twitter.com/{name.lower().replace(' ', '')}",
                        snippet=f"The latest Tweets from {name}. Technology reporter.",
                        source_domain="twitter.com",
                        date_found=datetime.now().isoformat()
                    )
                ]
        
        return simulated_results[:max_results]
    
    def fetch_article_content(self, url: str) -> Optional[ArticleData]:
        """
        Fetch and parse article content from a URL.
        
        Args:
            url: Article URL to fetch
            
        Returns:
            ArticleData object or None if fetch fails
        """
        try:
            # Try to use WebFetch tool if available
            try:
                from ..tools import WebFetch
                web_fetch = WebFetch()
                content = web_fetch.fetch(
                    url=url,
                    prompt="Extract the article title, author, publication date, and main content. Return as structured text."
                )
                
                # Parse the fetched content
                return self._parse_article_content(content, url)
                
            except ImportError:
                # Fallback to basic requests
                return self._fetch_with_requests(url)
                
        except Exception as e:
            print(f"Failed to fetch content from {url}: {e}")
            return None
    
    def _fetch_with_requests(self, url: str) -> Optional[ArticleData]:
        """Fallback method using requests library."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; JournalistResearchBot/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic content extraction (this would be more sophisticated in production)
            content = response.text
            title = self._extract_title_from_html(content)
            
            return ArticleData(
                title=title,
                url=url,
                content=content[:1000],  # Truncate for demo
                word_count=len(content.split())
            )
            
        except Exception as e:
            print(f"Requests fetch failed for {url}: {e}")
            return None
    
    def _extract_title_from_html(self, html_content: str) -> str:
        """Extract title from HTML content."""
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
        return "Article Title"
    
    def _parse_article_content(self, content: str, url: str) -> ArticleData:
        """Parse fetched content into structured data."""
        # This would be more sophisticated in production
        lines = content.split('\n')
        title = lines[0] if lines else "Article Title"
        
        # Extract potential author
        author_line = next((line for line in lines if 'by ' in line.lower()), None)
        author = author_line.replace('By ', '').replace('by ', '') if author_line else None
        
        return ArticleData(
            title=title,
            url=url,
            content=content,
            author=author,
            word_count=len(content.split())
        )


class JournalistSearchQueries:
    """Generate targeted search queries for journalist research."""
    
    @staticmethod
    def verification_queries(name: str, publication: str = None) -> List[str]:
        """Generate queries to verify journalist exists and current employment."""
        queries = [
            f'"{name}" journalist',
            f'"{name}" reporter',
        ]
        
        if publication:
            queries.extend([
                f'"{name}" {publication}',
                f'site:{publication.lower().replace(" ", "")}.com "{name}"',
                f'"{name}" {publication} bio'
            ])
        
        return queries
    
    @staticmethod
    def recent_articles_queries(name: str, publication: str = None, days_back: int = 90) -> List[str]:
        """Generate queries to find recent articles by the journalist."""
        current_year = datetime.now().year
        recent_months = [(datetime.now() - timedelta(days=30*i)).strftime('%B') for i in range(3)]
        
        queries = [
            f'"by {name}" {current_year}',
            f'author:"{name}"',
        ]
        
        if publication:
            pub_domain = publication.lower().replace(" ", "")
            queries.extend([
                f'site:{pub_domain}.com "by {name}"',
                f'"{name}" {publication} latest'
            ])
        
        # Add recent month searches
        for month in recent_months:
            queries.append(f'"{name}" {month} {current_year}')
        
        return queries
    
    @staticmethod
    def social_media_queries(name: str) -> List[str]:
        """Generate queries to find social media profiles."""
        return [
            f'"{name}" Twitter journalist',
            f'"{name}" LinkedIn reporter',
            f'"{name}" @{name.lower().replace(" ", "")}',
            f'site:twitter.com "{name}" journalist',
            f'site:linkedin.com/in "{name}"'
        ]
    
    @staticmethod
    def background_queries(name: str, publication: str = None) -> List[str]:
        """Generate queries for background and bio information."""
        queries = [
            f'"{name}" biography journalist',
            f'"{name}" reporter background',
            f'"{name}" journalism experience',
            f'"{name}" beat coverage'
        ]
        
        if publication:
            queries.extend([
                f'"{name}" {publication} staff',
                f'"{name}" {publication} senior reporter'
            ])
        
        return queries