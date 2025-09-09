"""AI service for handling GPT interactions."""

import json
import random
from typing import Dict, List, Any, Optional, AsyncGenerator
from pathlib import Path

import g4f

from config import config
from database import db_manager
from utils.exceptions import AIProviderError, ValidationError
from utils.logging import logger
from utils.http_utils import safe_api_call, TimeoutConfig
from utils.helpers import (
    load_json_file, 
    clean_response_sources, 
    select_random_proxy,
    create_dummy_cookies
)
from utils.provider_monitor import provider_monitor
from utils.validation import validate_provider, validate_model

class AIService:
    """Service for handling AI interactions."""
    
    def __init__(self):
        self.db = db_manager
        self.config = config
    
    async def generate_response(
        self,
        message: str,
        username: str = "admin",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_history: bool = False,
        remove_sources: bool = True,
        use_proxies: bool = False,
        cookie_file: Optional[str] = None
    ) -> str:
        """Generate AI response.
        
        Args:
            message: User message
            username: Username for context
            provider: AI provider override
            model: AI model override
            system_prompt: System prompt override
            use_history: Whether to use chat history
            remove_sources: Whether to remove source references
            use_proxies: Whether to use proxies
            cookie_file: Cookie file path
            
        Returns:
            AI response text
            
        Raises:
            AIProviderError: If AI generation fails
            ValidationError: If parameters are invalid
        """
        try:
            # Get user settings
            if username == "admin":
                settings = self.db.get_settings()
                user_settings = {
                    "provider": provider or settings.get("provider", self.config.api.default_provider),
                    "model": model or settings.get("model", self.config.api.default_model),
                    "system_prompt": system_prompt or settings.get("system_prompt", ""),
                    "message_history": use_history and settings.get("message_history", False)
                }
            else:
                user_data = self.db.get_user_by_username(username)
                if not user_data:
                    raise ValidationError(f"User '{username}' not found")
                
                user_settings = {
                    "provider": provider or user_data.get("provider", self.config.api.default_provider),
                    "model": model or user_data.get("model", self.config.api.default_model),
                    "system_prompt": system_prompt or user_data.get("system_prompt", ""),
                    "message_history": use_history and user_data.get("message_history", False)
                }
            
            # Validate provider and model
            is_valid, error_msg = validate_provider(user_settings["provider"], self.config.available_providers)
            if not is_valid:
                raise ValidationError(error_msg)
            
            is_valid, error_msg = validate_model(user_settings["model"])
            if not is_valid:
                raise ValidationError(error_msg)
            
            # Prepare chat history
            chat_history = self._prepare_chat_history(
                message=message,
                username=username,
                system_prompt=user_settings["system_prompt"],
                use_history=user_settings["message_history"]
            )
            
            # Prepare cookies
            cookies = self._load_cookies(cookie_file)
            
            # Prepare proxy
            proxy = self._get_proxy() if use_proxies else None
            
            # Generate response
            response_text = await self._call_ai_api(
                chat_history=chat_history,
                provider=user_settings["provider"],
                model=user_settings["model"],
                cookies=cookies,
                proxy=proxy
            )
            
            # Clean response if needed
            if remove_sources:
                response_text = clean_response_sources(response_text)
            
            # Save chat history if enabled
            if user_settings["message_history"]:
                chat_history.append({"role": "assistant", "content": response_text})
                self.db.save_chat_history(username, json.dumps(chat_history))
            
            logger.info(f"AI response generated for user '{username}' using provider '{user_settings['provider']}'")
            return response_text
            
        except (ValidationError, AIProviderError):
            raise
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            raise AIProviderError(f"AI generation failed: {e}")
    
    def _prepare_chat_history(
        self,
        message: str,
        username: str,
        system_prompt: str,
        use_history: bool
    ) -> List[Dict[str, str]]:
        """Prepare chat history for AI request.
        
        Args:
            message: Current user message
            username: Username
            system_prompt: System prompt
            use_history: Whether to load previous history
            
        Returns:
            List of chat messages
        """
        chat_history = []
        
        # Add system prompt if provided
        if system_prompt:
            chat_history.append({"role": "system", "content": system_prompt})
        
        # Load previous history if enabled
        if use_history:
            history_json = self.db.get_chat_history(username)
            if history_json:
                try:
                    previous_history = json.loads(history_json)
                    # Remove system prompt from previous history to avoid duplication
                    previous_history = [msg for msg in previous_history if msg.get("role") != "system"]
                    chat_history.extend(previous_history)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid chat history JSON for user '{username}'")
        
        # Add current message
        chat_history.append({"role": "user", "content": message})
        
        return chat_history
    
    def _load_cookies(self, cookie_file: Optional[str]) -> Dict[str, str]:
        """Load cookies from file.
        
        Args:
            cookie_file: Path to cookie file
            
        Returns:
            Dictionary of cookies
        """
        if not cookie_file:
            return create_dummy_cookies()
        
        cookie_path = Path(cookie_file)
        cookies = load_json_file(cookie_path, {})
        
        if not cookies:
            logger.warning(f"No cookies found in {cookie_file}, using dummy cookies")
            return create_dummy_cookies()
        
        logger.debug(f"Loaded {len(cookies)} cookies from {cookie_file}")
        return cookies
    
    def _get_proxy(self) -> Optional[str]:
        """Get random proxy from configuration.
        
        Returns:
            Proxy URL or None
        """
        proxies_path = Path(self.config.files.proxies_file)
        proxies = load_json_file(proxies_path, [])
        
        if not proxies:
            logger.warning("No proxies configured")
            return None
        
        proxy_url = select_random_proxy(proxies)
        if proxy_url:
            logger.debug(f"Using proxy: {proxy_url.split('@')[0]}@***")  # Mask credentials
        
        return proxy_url
    
    async def _call_ai_api(
        self,
        chat_history: List[Dict[str, str]],
        provider: str,
        model: str,
        cookies: Dict[str, str],
        proxy: Optional[str]
    ) -> str:
        """Call AI API to generate response.
        
        Args:
            chat_history: Chat message history
            provider: AI provider
            model: AI model
            cookies: Request cookies
            proxy: Proxy URL
            
        Returns:
            AI response text
            
        Raises:
            AIProviderError: If API call fails
        """
        # Check if provider is blacklisted
        if provider_monitor.is_provider_blacklisted(provider):
            logger.warning(f"Provider '{provider}' is blacklisted, using fallback")
            provider = "Auto"
        
        # Get reliable providers for fallback
        reliable_providers = provider_monitor.get_reliable_providers(self.config.available_providers)
        
        # Try original provider first
        if provider != "Auto":
            ai_provider = self.config.available_providers.get(provider)
            if ai_provider:
                logger.info(f"Attempting with provider: {provider}")
                response = await self._make_api_call(chat_history, ai_provider, model, cookies, proxy, provider)
                if response:
                    provider_monitor.record_success(provider)
                    return response
                else:
                    provider_monitor.record_failure(provider, "no_response")
        
        # Try Auto mode
        logger.info("Attempting with Auto mode")
        response = await self._make_api_call(chat_history, None, model, cookies, proxy, "Auto")
        if response:
            provider_monitor.record_success("Auto")
            return response
        else:
            provider_monitor.record_failure("Auto", "no_response")
        
        # Try reliable providers as fallback
        logger.warning("Auto mode failed, trying reliable providers")
        for fallback_provider in reliable_providers[:3]:  # Try top 3 reliable providers
            try:
                ai_provider = self.config.available_providers.get(fallback_provider)
                if ai_provider:
                    logger.info(f"Attempting reliable fallback: {fallback_provider}")
                    response = await self._make_api_call(chat_history, ai_provider, model, cookies, proxy, fallback_provider)
                    if response:
                        provider_monitor.record_success(fallback_provider)
                        logger.info(f"Successfully used reliable fallback: {fallback_provider}")
                        return response
                    else:
                        provider_monitor.record_failure(fallback_provider, "no_response")
            except Exception as e:
                provider_monitor.record_failure(fallback_provider, "exception")
                logger.warning(f"Reliable fallback {fallback_provider} failed: {e}")
                continue
        
        # Last resort: try any healthy provider
        healthy_providers = provider_monitor.get_healthy_providers(self.config.available_providers)
        logger.warning("Reliable providers failed, trying any healthy provider")
        
        for fallback_provider in healthy_providers[:5]:  # Try up to 5 healthy providers
            if fallback_provider in reliable_providers:
                continue  # Already tried
            
            try:
                ai_provider = self.config.available_providers.get(fallback_provider)
                if ai_provider:
                    logger.info(f"Attempting healthy fallback: {fallback_provider}")
                    response = await self._make_api_call(chat_history, ai_provider, model, cookies, proxy, fallback_provider)
                    if response:
                        provider_monitor.record_success(fallback_provider)
                        logger.info(f"Successfully used healthy fallback: {fallback_provider}")
                        return response
                    else:
                        provider_monitor.record_failure(fallback_provider, "no_response")
            except Exception as e:
                provider_monitor.record_failure(fallback_provider, "exception")
                logger.warning(f"Healthy fallback {fallback_provider} failed: {e}")
                continue
        
        # Log provider status summary for debugging
        status_summary = provider_monitor.get_status_summary()
        logger.error(f"All providers failed. Status summary: {status_summary}")
        
        raise AIProviderError("All providers failed to generate a response")
    
    async def _make_api_call(
        self,
        chat_history: List[Dict[str, str]],
        ai_provider,
        model: str,
        cookies: Dict[str, str],
        proxy: Optional[str],
        provider_name: str = "Unknown"
    ) -> Optional[str]:
        """Make a single API call to g4f.
        
        Args:
            chat_history: Chat message history
            ai_provider: AI provider object or None for Auto
            model: AI model
            cookies: Request cookies
            proxy: Proxy URL
            provider_name: Name of provider for logging
            
        Returns:
            AI response text or None if failed
        """
        
        async def make_request():
            if ai_provider is None:  # Auto mode
                return await g4f.ChatCompletion.create_async(
                    model=model,
                    messages=chat_history,
                    cookies=cookies,
                    proxy=proxy
                )
            else:
                return await g4f.ChatCompletion.create_async(
                    model=model,
                    provider=ai_provider,
                    messages=chat_history,
                    cookies=cookies,
                    proxy=proxy
                )
        
        try:
            # Use safe_api_call with timeout and retry logic
            response = await safe_api_call(
                make_request,
                timeout=TimeoutConfig.DEFAULT_TIMEOUT,
                max_retries=1  # Only 1 retry per provider to fail fast
            )
            
            if response is None:
                logger.warning(f"Provider {provider_name} returned no response")
                return None
            
            # Collect response
            response_text = ""
            
            # Handle both string responses and async generators
            if hasattr(response, '__aiter__'):
                # It's an async generator
                import asyncio
                try:
                    async for chunk in response:
                        response_text += str(chunk)
                        # Add small delay to prevent blocking and allow timeout handling
                        await asyncio.sleep(0.001)
                except Exception as e:
                    logger.warning(f"Error reading streaming response from {provider_name}: {e}")
                    return None
            else:
                # It's already a string
                response_text = str(response)
            
            if not response_text or response_text.strip() == "":
                logger.warning(f"Empty response from provider {provider_name}")
                return None
            
            logger.debug(f"Received response of {len(response_text)} characters from {provider_name}")
            return response_text
            
        except Exception as e:
            error_msg = str(e).lower()
            error_type = "unknown"
            
            if "401" in error_msg or "unauthorized" in error_msg:
                error_type = "unauthorized"
                logger.warning(f"Provider {provider_name} returned unauthorized error: {e}")
            elif "chrome" in error_msg or "browser" in error_msg:
                error_type = "browser_required"
                logger.warning(f"Provider {provider_name} requires browser but none found: {e}")
            elif "timeout" in error_msg or "too slow" in error_msg:
                error_type = "timeout"
                logger.warning(f"Provider {provider_name} connection timeout: {e}")
            elif "connection" in error_msg or "network" in error_msg:
                error_type = "network"
                logger.warning(f"Provider {provider_name} network error: {e}")
            else:
                logger.warning(f"Provider {provider_name} failed with error: {e}")
            
            # Record failure in monitor
            provider_monitor.record_failure(provider_name, error_type)
            return None
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get available models for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of available models
        """
        if provider == "Auto":
            return self.config.generic_models
        
        try:
            provider_obj = self.config.available_providers.get(provider)
            if provider_obj and hasattr(provider_obj, 'models'):
                return list(provider_obj.models)
            return ["default"]
        except Exception as e:
            logger.warning(f"Could not get models for provider '{provider}': {e}")
            return ["default"]

# Global AI service instance
ai_service = AIService()
