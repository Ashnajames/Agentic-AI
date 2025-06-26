from typing import List, Dict, Any, Optional
import torch
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    pipeline, BitsAndBytesConfig
)
from app.core.config import settings
from app.core.logging import setup_logging
import os
import re

logger = setup_logging()

class GenerationService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.model_name = settings.HF_MODEL_NAME
        self.device = settings.DEVICE
        self.cache_dir = settings.HF_CACHE_DIR

    async def initialize(self):
        try:
            logger.info(f"Loading generation model: {self.model_name}")

            is_local_model = os.path.exists(self.model_name)
            model_kwargs = {
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "low_cpu_mem_usage": True,
            }
            if not is_local_model:
                model_kwargs["cache_dir"] = self.cache_dir

            if self.device == "cuda" and "large" in self.model_name.lower():
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                model_kwargs["quantization_config"] = quantization_config

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=None if is_local_model else self.cache_dir,
                use_auth_token=None if is_local_model else settings.HF_TOKEN
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                use_auth_token=None if is_local_model else settings.HF_TOKEN,
                **model_kwargs
            )

            if self.device != "cpu" and not any("quantization_config" in str(k) for k in model_kwargs.keys()):
                self.model = self.model.to(self.device)

            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )

            logger.info("Generation model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load generation model: {e}")
            await self._load_fallback_model()

    async def _load_fallback_model(self):
        try:
            logger.info("Loading fallback model: microsoft/DialoGPT-small")

            self.tokenizer = AutoTokenizer.from_pretrained(
                "microsoft/DialoGPT-small",
                cache_dir=self.cache_dir
            )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.model = AutoModelForCausalLM.from_pretrained(
                "microsoft/DialoGPT-small",
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32
            )

            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=-1,
            )

            logger.info("Fallback model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            raise

    async def generate_response(self, 
                              query: str, 
                              context_documents: List[Dict[str, Any]],
                              conversation_history: Optional[List[Dict[str, str]]] = None,
                              max_length: int = 8019) -> str:
        if not self.pipeline:
            raise RuntimeError("Generation model not initialized")

        try:
            logger.info(f"Retrieved context documents: {context_documents}")
            context = self._prepare_context(context_documents)
            prompt = self._build_prompt(query, context, conversation_history)

            result = self.pipeline(
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
                length_penalty=1.0,
            )

            generated_text = result[0]['generated_text']
            response = self._extract_response(generated_text, prompt)

            logger.info(f"Generated response for query: {query[:50]}...")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(query, context_documents)

    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        context_parts = []

        for i, doc in enumerate(documents[:5]):
            tool_name = doc.get('tool_name', 'Unknown')
            category = doc.get('category', 'general')
            content = doc.get('content', '')
            context_parts.append(f"Source {i+1} ({tool_name} - {category}): {content}")

        return '\n\n'.join(context_parts)

    def _build_prompt(self, 
                     query: str, 
                     context: str, 
                     conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        system_prompt = """You are a helpful and knowledgeable assistant. Use only the information provided in the documents below to answer the user's question.create a conscise and complete answer based on the provided information. You are only allowed to answer questions that are within the domain of the documents provided.
        If the question is outside this domain, or the answer is not present in the documents, respond with: "I don't know".
    
[DOCUMENTS]
{context}

[QUESTION]
{query}

[ANSWER]"""

        if conversation_history:
            history_text = ""
            for msg in conversation_history[-3:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                history_text += f"{role.title()}: {content}\n"

            system_prompt = f"Previous conversation:\n{history_text}\n\n{system_prompt}"

        return system_prompt.format(context=context, query=query)

    def _extract_response(self, generated_text: str, prompt: str) -> str:
        if prompt in generated_text:
            response = generated_text.replace(prompt, "").strip()
        else:
            response = generated_text.strip()

        lines = response.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith(('Question:', 'Answer:', 'Context:')):
                cleaned_lines.append(line)

        response = '\n'.join(cleaned_lines)

        max_response_length = 10000
        if len(response) > max_response_length:
            sentences = response.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence) < max_response_length:
                    truncated += sentence + ". "
                else:
                    break
            response = truncated.strip()

        
        response = self._remove_incomplete_sentences(response)

        return response if response else "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."

    def _remove_incomplete_sentences(self, text: str) -> str:
        """Remove trailing sentence if it seems incomplete (e.g. no punctuation, cutoff mid-word)"""
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        if sentences and not re.search(r'[.!?]["\']?$', sentences[-1]):
            sentences.pop()
        return ' '.join(sentences)

    def _generate_fallback_response(self, query: str, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return "I don't have enough information to answer your question. Please try asking about specific ITSM tools or features."

        tools_mentioned = set()
        categories = set()

        for doc in documents[:5]:
            tool_name = doc.get('tool_name', '')
            category = doc.get('category', '')

            if tool_name and tool_name != 'all':
                tools_mentioned.add(tool_name)
            if category:
                categories.add(category)

        response_parts = [
            "Based on the available information:",
        ]

        if tools_mentioned:
            response_parts.append(f"Relevant ITSM tools: {', '.join(tools_mentioned)}")

        first_doc = documents[0]
        content = first_doc.get('content', '')
        if content:
            summary = content[:1024] + "..." if len(content) > 200 else content
            response_parts.append(f"Key information: {summary}")

        return '\n\n'.join(response_parts)

    def is_ready(self) -> bool:
        return self.pipeline is not None


generation_service = GenerationService()
