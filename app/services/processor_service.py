import re
from typing import List, Dict, Any
from datetime import datetime
from app.core.config import settings
from app.core.logging import setup_logging

# Assuming you have partition_html and chunk_elements imported
from unstructured.partition.html import partition_html
from unstructured.chunking.basic import chunk_elements

logger = setup_logging()


def extract_and_chunk_text_from_html(html_content):
    """Extract and chunk text from an HTML article."""
    try:
        elements = partition_html(text=html_content)
        narrative_elements = [el for el in elements if el.category == "NarrativeText"]
        chunks = chunk_elements(narrative_elements, max_characters=1400)
        chunked_texts = [" ".join(str(chunk)) for chunk in chunks]
        return chunked_texts
    except Exception as e:
        logger.error(f"Error extracting and chunking text: {e}")
        return []


class ProcessorService:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def process_scraped_content(self, scraped_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        documents = []
        timestamp = datetime.utcnow().isoformat(timespec='seconds') + 'Z'

        try:
            for section in scraped_data.get('sections', []):
                docs = await self._process_section(section, scraped_data['url'], timestamp)
                documents.extend(docs)

            for tool in scraped_data.get('tools', []):
                docs = await self._process_tool(tool, scraped_data['url'], timestamp)
                documents.extend(docs)

            overview_doc = await self._create_overview_document(scraped_data, timestamp)
            documents.append(overview_doc)

            logger.info(f"Processed {len(documents)} documents from scraped content")
            return documents

        except Exception as e:
            logger.error(f"Error processing scraped content: {e}")
            return []

    async def _process_section(self, section: Dict[str, Any], source_url: str, timestamp: str) -> List[Dict[str, Any]]:
        documents = []
        content = section.get('content', '')
        title = section.get('title', '')

        if not content.strip():
            return documents

        full_content = f"Section: {title}\n\n{content}" if title else content

        # Check if the content is HTML and use HTML-specific chunking
        if self._is_html(content):
            chunks = extract_and_chunk_text_from_html(content)
        else:
            chunks = await self._split_text_into_chunks(full_content)

        for i, chunk in enumerate(chunks):
            documents.append({
                'content': chunk,
                'source': source_url,
                'category': 'section',
                'section': title,
                'chunk_index': i,
                'tool_name': self._extract_tool_name_from_title(title),
                'timestamp': timestamp
            })

        return documents

    async def _process_tool(self, tool: Dict[str, Any], source_url: str, timestamp: str) -> List[Dict[str, Any]]:
        documents = []

        tool_name = tool.get('name', '')
        if not tool_name:
            return documents

        main_content = self._build_tool_overview(tool)
        documents.append({
            'content': main_content,
            'source': source_url,
            'category': 'tool_overview',
            'tool_name': tool_name,
            'tool_rank': tool.get('rank', 0),
            'timestamp': timestamp
        })

        details = tool.get('details', {})
        aspects = {
            'pricing': details.get('pricing', ''),
            'features': ', '.join(details.get('features', [])),
            'pros': ', '.join(details.get('pros', [])),
            'cons': ', '.join(details.get('cons', [])),
            'rating': details.get('rating', ''),
            'best_for': details.get('best_for', '')
        }

        for aspect, value in aspects.items():
            if value and value.strip():
                aspect_content = f"{tool_name} - {aspect.replace('_', ' ').title()}: {value}"
                documents.append({
                    'content': aspect_content,
                    'source': source_url,
                    'category': f'tool_{aspect}',
                    'tool_name': tool_name,
                    'tool_rank': tool.get('rank', 0),
                    'aspect': aspect,
                    'timestamp': timestamp
                })

        return documents

    def _build_tool_overview(self, tool: Dict[str, Any]) -> str:
        name = tool.get('name', '')
        rank = tool.get('rank', 0)
        description = tool.get('description', '')
        details = tool.get('details', {})

        content_parts = [
            f"ITSM Tool: {name}",
            f"Ranking: #{rank}" if rank > 0 else "",
            f"Description: {description}" if description else "",
        ]

        if details.get('features'):
            content_parts.append(f"Key Features: {', '.join(details['features'])}")

        if details.get('pricing'):
            content_parts.append(f"Pricing: {details['pricing']}")

        if details.get('rating'):
            content_parts.append(f"Rating: {details['rating']}")

        if details.get('best_for'):
            content_parts.append(f"Best For: {details['best_for']}")

        if details.get('pros'):
            content_parts.append(f"Pros: {', '.join(details['pros'])}")

        if details.get('cons'):
            content_parts.append(f"Cons: {', '.join(details['cons'])}")

        return '\n\n'.join(filter(None, content_parts))

    async def _create_overview_document(self, scraped_data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        title = scraped_data.get('title', 'ITSM Tools Guide')
        url = scraped_data.get('url', '')

        overview_content = f"""
{title}

Source: {url}

This comprehensive guide covers the top ITSM (IT Service Management) tools for 2025, providing detailed analysis of features, pricing, deployment options, and use cases.

Tools Covered:
"""

        for tool in scraped_data.get('tools', []):
            name = tool.get('name', '')
            rank = tool.get('rank', 0)
            description = tool.get('description', '')
            if name:
                overview_content += f"\n{rank}. {name}"
                if description:
                    overview_content += f" - {description}"

        overview_content += "\n\nKey Topics Covered:"
        for section in scraped_data.get('sections', []):
            title = section.get('title', '')
            if title and len(title) < 100 and not title.lower().startswith(('1.', '2.', '3.')):
                overview_content += f"\n- {title}"

        return {
            'content': overview_content.strip(),
            'source': url,
            'category': 'overview',
            'tool_name': 'all',
            'timestamp': timestamp
        }

    async def _split_text_into_chunks(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                sentence_ends = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                best_break = -1
                for sentence_end in sentence_ends:
                    pos = text.rfind(sentence_end, start + self.chunk_size // 2, end)
                    if pos > best_break:
                        best_break = pos + len(sentence_end)
                if best_break > start + self.chunk_size // 2:
                    end = best_break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = max(start + self.chunk_size - self.chunk_overlap, end - self.chunk_overlap)
            if start >= len(text) - 10:
                break

        return chunks

    def _extract_tool_name_from_title(self, title: str) -> str:
        match = re.match(r'\d+\.\s*([A-Za-z][A-Za-z\s&\-]+)', title)
        if match:
            return match.group(1).strip()

        known_tools = [
            'Xurrent', '4me', 'ServiceNow', 'Jira Service Management', 'Jira',
            'BMC Helix', 'BMC', 'Freshservice', 'SolarWinds', 'ManageEngine',
            'Ivanti', 'Zendesk', 'SysAid', 'Remedy'
        ]

        title_lower = title.lower()
        for tool in known_tools:
            if tool.lower() in title_lower:
                return tool

        return ''

    def _is_html(self, text: str) -> bool:
        return any(tag in text.lower() for tag in ['<html', '<div', '<p', '<section', '<article'])
