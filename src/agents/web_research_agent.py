from typing import Any, Dict, List
from datetime import datetime
import os
import json
import aiohttp
from .base_agent import BaseAgent
from ..models.report import ResearchResult

RESEARCH_SYSTEM_PROMPT = """You are an expert research assistant with access to real-time web search via the Perplexity API. Your task is to:
1. Search the web for accurate, up-to-date information from reliable sources
2. Evaluate source credibility (prefer academic, news, and established websites)
3. Extract key facts and insights based on current information
4. Provide URLs and attribution for all information sources
5. Synthesize information into comprehensive, well-structured answers

Your response MUST be formatted in well-structured Markdown, including:
- Clear **headings** (# for main headings) and **subheadings** (## or ###) to organize content
- **Bulleted lists** (- item) or **numbered lists** (1. item) for sequential information
- **Tables** using proper Markdown syntax (| Header | Header |) when presenting comparative data
- **Bold** (**text**) for emphasis on key points and terminology
- *Italic* (*text*) for definitions or secondary emphasis
- `Code blocks` for technical terms or snippets when relevant
- > Blockquotes for direct quotations from sources

Always cite your sources by providing the source title and URL where possible. Be transparent about the reliability and recency of information."""

class WebResearchAgent(BaseAgent):
    """Agent responsible for conducting web research using Perplexity API."""
    
    async def execute(self, task: Dict[str, Any]) -> List[ResearchResult]:
        """Execute research tasks for given questions.
        
        Args:
            task (Dict[str, Any]): The research task containing questions
            
        Returns:
            List[ResearchResult]: The research results
        """
        questions = task["questions"]
        context = task.get("context", "")
        results = []
        
        for question in questions:
            try:
                # Use Perplexity API for research
                research = await self._research_question(question, context)
                
                # Evaluate credibility
                credibility_score = await self._evaluate_credibility(research)
                
                result = ResearchResult(
                    source="Perplexity Research",
                    content=research["answer"],
                    credibility_score=credibility_score,
                    timestamp=datetime.utcnow().isoformat(),
                    metadata={
                        "question": question,
                        "context": context,
                        "citations": research.get("citations", [])
                    }
                )
                
                results.append(result)
                
                # Save research as markdown file
                await self._save_research_as_markdown(question, research["answer"])
                
            except Exception as e:
                self.logger.error(f"Error researching question '{question}': {str(e)}")
                # Continue with next question on error
                continue
        
        return results
    
    async def _research_question(self, question: str, context: str) -> Dict[str, Any]:
        """Research a question using Perplexity API.
        
        Args:
            question (str): The research question
            context (str): Additional context
            
        Returns:
            Dict[str, Any]: The research results
        """
        # Construct the query with the context if available
        query = question
        if context:
            query = f"{question}\nContext: {context}"
            
        try:
            # Call Perplexity API
            perplexity_response = await self._call_perplexity_api(query)
            
            # Extract the answer from the response
            content = perplexity_response["choices"][0]["message"]["content"]
            
            # Extract any citations from the response
            citations = []
            if "references" in perplexity_response:
                for ref in perplexity_response["references"]:
                    if "title" in ref and "url" in ref:
                        citation_text = f"[{ref['title']}, {ref['url']}]"
                        citations.append(citation_text)
            else:
                # Fall back to extracting citations from text
                citations = self._extract_citations(content)
            
            # Structure the response
            return {
                "answer": content,
                "citations": citations,
                "reliability": "Based on real-time web search results from Perplexity API"
            }
        except Exception as e:
            self.logger.error(f"Error researching question '{question}': {str(e)}")
            raise
    
    async def _call_perplexity_api(self, query: str, model: str = "sonar-reasoning-pro", recency: str = "year") -> Dict[str, Any]:
        """Call the Perplexity API with the given query.
        
        Args:
            query (str): The query to send to Perplexity
            model (str, optional): The Perplexity model to use. Defaults to "sonar-reasoning-pro".
            recency (str, optional): Time filter for search results. Defaults to "year".
            
        Returns:
            Dict[str, Any]: The API response
        """
        # Get the API key from environment variables
        api_key = os.environ.get("PERPLEXITY_API_KEY")
        if not api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            "temperature": 0.3,
            "search_recency_filter": recency,
            "max_tokens": 4000,
            "return_citations": True
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post("https://api.perplexity.ai/chat/completions", 
                                       headers=headers, 
                                       json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"Perplexity API error: {response.status} - {error_text}")
                    
                    return await response.json()
            except Exception as e:
                self.logger.error(f"Error calling Perplexity API: {str(e)}")
                raise
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract citations from the research text.
        
        Args:
            text (str): The research text
            
        Returns:
            List[str]: List of citations
        """
        # Simple citation extraction - could be improved
        citations = []
        lines = text.split("\n")
        for line in lines:
            if "[" in line and "]" in line:
                start = line.find("[")
                end = line.find("]", start) + 1
                citation = line[start:end]
                if citation not in citations:
                    citations.append(citation)
        return citations
    
    async def _evaluate_credibility(self, research: Dict[str, Any]) -> float:
        """Evaluate the credibility of research results from Perplexity API.
        
        Args:
            research (Dict[str, Any]): The research results
            
        Returns:
            float: Credibility score between 0 and 1
        """
        # More nuanced credibility scoring for Perplexity API results
        score = 0.6  # Higher base score due to Perplexity's real-time web search
        
        # Add points for citations - Perplexity citations are direct from the web
        if research.get("citations"):
            citation_count = len(research.get("citations", []))
            # More citations is better, but with diminishing returns
            citation_score = min(0.3, citation_count * 0.06)
            score += citation_score
        
        # Add points for answer length/detail
        answer_length = len(research.get("answer", "").split())
        if answer_length > 300:
            score += 0.2
        elif answer_length > 150:
            score += 0.1
        
        # Check for diverse sources
        unique_domains = set()
        for citation in research.get("citations", []):
            # Try to extract domain from citation
            if "http" in citation:
                try:
                    start = citation.find("http")
                    end = citation.find(" ", start)
                    if end == -1:
                        end = citation.find("]", start)
                    url = citation[start:end]
                    # Simple domain extraction
                    parts = url.split("/")
                    if len(parts) > 2:
                        domain = parts[2]  # After http:// comes domain
                        unique_domains.add(domain)
                except:
                    pass
        
        # Add points for diverse sources
        diversity_score = min(0.2, len(unique_domains) * 0.05)
        score += diversity_score
        
        return min(1.0, score)
    
    async def _save_research_as_markdown(self, question: str, content: str) -> None:
        """Save research results as markdown file.
        
        Args:
            question (str): The research question
            content (str): The content to save
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs("output/research", exist_ok=True)
            
            # Generate a filename based on the question
            filename = os.path.join("output/research", f"{self._generate_filename(question)}.md")
            
            # Write the content to the file
            with open(filename, "w", encoding="utf-8") as f:
                # Add a header with the question
                f.write(f"# Research: {question}\n\n")
                f.write(f"*Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
                f.write(content)
                
            self.logger.debug(f"Saved research for '{question}' to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving research as markdown: {str(e)}")
    
    def _generate_filename(self, text: str) -> str:
        """Generate a valid filename from text.
        
        Args:
            text (str): The text to convert to a filename
            
        Returns:
            str: A valid filename
        """
        # Remove invalid characters and replace spaces with underscores
        filename = "".join(c if c.isalnum() or c in " -_" else "_" for c in text)
        filename = filename.replace(" ", "_")
        
        # Truncate if too long
        if len(filename) > 100:
            filename = filename[:100]
            
        # Add timestamp to make it unique
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{filename}_{timestamp}" 