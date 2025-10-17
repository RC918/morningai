#!/usr/bin/env python3
"""
Browser Tool - Browser automation via Playwright
"""
import asyncio
import logging
from typing import Dict, Any
from playwright.async_api import async_playwright

class BrowserTool:
    """Browser automation tool"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.playwright = None
        self.browser = None
    
    def requires_approval(self, arguments: Dict[str, Any]) -> bool:
        """Browser actions generally don't require approval"""
        return False
    
    def get_approval_description(self, arguments: Dict[str, Any]) -> str:
        """Get human-readable description for approval"""
        return f"Browser action: {arguments}"
    
    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser action"""
        url = arguments.get('url', '')
        action = arguments.get('action', 'navigate')
        
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True
                )
            
            page = await self.browser.new_page()
            
            if action == 'navigate':
                await page.goto(url, timeout=30000)
                content = await page.content()
                title = await page.title()
                
                await page.close()
                
                return {
                    'title': title,
                    'url': page.url,
                    'content_length': len(content)
                }
            
            await page.close()
            return {'status': 'success'}
            
        except Exception as e:
            self.logger.error(f"Browser action failed: {e}")
            return {'error': str(e)}
