import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()

class ScraperService:
    def __init__(self):
        self.timeout = settings.SCRAPING_TIMEOUT
        self.delay = settings.SCRAPING_DELAY
        self.max_retries = settings.MAX_RETRIES
        
    async def scrape_itsm_content(self, url: str = None) -> Optional[Dict[str, Any]]:
        """Scrape ITSM content from the specified URL"""
        target_url = url or settings.TARGET_URL
        
        try:
            logger.info(f"Scraping content from: {target_url}")
            
            async with aiohttp.ClientSession() as session:
                content = await self._fetch_with_retry(session, target_url)
                
            if not content:
                return None
                
            
            soup = BeautifulSoup(content, 'html.parser')
            
          
            scraped_data = await self._extract_structured_content(soup, target_url)
            
            logger.info(f"Successfully scraped {len(scraped_data.get('sections', []))} sections")
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping content: {e}")
            return None
    
    async def _fetch_with_retry(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch URL content with retry logic"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} on attempt {attempt + 1}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.delay * (attempt + 1))
        
        logger.error(f"All {self.max_retries} attempts failed for {url}")
        return None
    
    async def _extract_structured_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract and structure content from the webpage"""
        content_data = {
            'url': url,
            'title': self._extract_title(soup),
            'sections': [],
            'tools': [],
            'metadata': self._extract_metadata(soup)
        }
        
   
        main_content = self._find_main_content(soup)
        if not main_content:
            return content_data
        

        sections = await self._extract_sections(main_content)
        content_data['sections'] = sections
      
        tools = await self._extract_tools(main_content)
        content_data['tools'] = tools
        
        return content_data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        selectors = ['title', 'h1', '.title', '.post-title']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return "ITSM Tools Guide"
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Find the main content area"""
        selectors = [
            'article', '.content', '.post-content', '.entry-content',
            '.blog-content', 'main', '.main-content', '[role="main"]'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content
        
        return soup.find('body')
    
    async def _extract_sections(self, content: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract content sections"""
        sections = []
        current_section = None
        
     
        elements = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'div'])
        
        for element in elements:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            
                if current_section and current_section.get('content', '').strip():
                    sections.append(current_section)
                
            
                current_section = {
                    'title': element.get_text().strip(),
                    'level': int(element.name[1]),
                    'content': '',
                    'type': 'section'
                }
            else:
               
                if current_section is not None:
                    text = element.get_text().strip()
                    if text and len(text) > 10: 
                        current_section['content'] += text + '\n\n'
        
        
        if current_section and current_section.get('content', '').strip():
            sections.append(current_section)
        
        return sections
    
    async def _extract_tools(self, content: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract ITSM tool information"""
        tools = []
        text_content = content.get_text()
        
       
        tool_pattern = r'(\d+)\.\s*([A-Za-z][A-Za-z\s&\-]+)(?:\s*[-–]\s*(.+?))?(?=\n|\r|$)'
        matches = re.finditer(tool_pattern, text_content, re.MULTILINE)
        
        for match in matches:
            rank = int(match.group(1))
            name = match.group(2).strip()
            description = match.group(3).strip() if match.group(3) else ""
            
            
            if len(name) < 3 or rank > 20:
                continue
            
            
            tool_details = await self._extract_tool_details(content, name)
            
            tools.append({
                'rank': rank,
                'name': name,
                'description': description,
                'details': tool_details
            })
        
        return tools
    
    async def _extract_tool_details(self, content: BeautifulSoup, tool_name: str) -> Dict[str, Any]:
        """Extract detailed information for a specific tool"""
        details = {
            'features': [],
            'pricing': '',
            'pros': [],
            'cons': [],
            'rating': '',
            'best_for': ''
        }
        
        text = content.get_text().lower()
        tool_name_lower = tool_name.lower()
        
        
        tool_start = text.find(tool_name_lower)
        if tool_start == -1:
            return details
        
       
        context_start = max(0, tool_start - 500)
        context_end = min(len(text), tool_start + 2000)
        tool_context = text[context_start:context_end]
        
        
        pricing_patterns = [
            r'pricing[:\s]*([^\n]{1,100})',
            r'price[:\s]*([^\n]{1,100})',
            r'cost[:\s]*([^\n]{1,100})',
            r'\$\d+[^\n]{0,50}'
        ]
        
        for pattern in pricing_patterns:
            match = re.search(pattern, tool_context)
            if match:
                details['pricing'] = match.group(0).strip()
                break
        
        
        rating_patterns = [
            r'(\d+\.?\d*)/5',
            r'(\d+\.?\d*)\s*stars?',
            r'rating[:\s]*(\d+\.?\d*)'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, tool_context)
            if match:
                details['rating'] = match.group(1)
                break
        
        return details
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata"""
        metadata = {}
        
       
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')
            if name and content:
                metadata[name] = content
        
       
        date_selectors = [
            'time[datetime]', '.published', '.date', '.post-date',
            '[datetime]', '.timestamp'
        ]
        
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                date_value = (
                    date_element.get('datetime') or 
                    date_element.get('content') or 
                    date_element.get_text().strip()
                )
                if date_value:
                    metadata['publish_date'] = date_value
                    break
        
        return metadata
