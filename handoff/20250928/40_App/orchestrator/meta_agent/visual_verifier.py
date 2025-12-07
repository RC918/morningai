"""
Visual Verifier - Headless Browser Screenshot and UI Verification

This module implements visual verification infrastructure for Meta Agent,
enabling headless browser screenshot capture and UI change validation.

Issue: #2073 - add Visual Verification infrastructure with headless browser
Milestone: M5 - Meta Agent Optimization

Background:
    Frontend projects already have Playwright configured:
    - handoff/20250928/40_App/owner-console/playwright.config.ts
    - handoff/20250928/40_App/frontend-dashboard/playwright.config.ts

    But orchestrator (handoff/20250928/40_App/orchestrator/) lacks headless
    browser testing capability.

Goals:
    1. Add headless browser support in vm_provisioner.py or new module
    2. Provide screenshot and visual comparison API
    3. Integrate into AutonomousExecutor for VERIFICATION task type
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of visual verification"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ScreenshotResult:
    """Result of a screenshot capture operation"""
    success: bool
    url: str
    screenshot_path: Optional[str] = None
    screenshot_bytes: Optional[bytes] = None
    selector: Optional[str] = None
    width: int = 0
    height: int = 0
    captured_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "success": self.success,
            "url": self.url,
            "screenshot_path": self.screenshot_path,
            "selector": self.selector,
            "width": self.width,
            "height": self.height,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class VerificationResult:
    """Result of a visual verification check"""
    status: VerificationStatus
    check_type: str
    passed: bool
    url: str
    selector: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    screenshot: Optional[ScreenshotResult] = None
    message: str = ""
    verified_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "status": self.status.value,
            "check_type": self.check_type,
            "passed": self.passed,
            "url": self.url,
            "selector": self.selector,
            "expected": self.expected,
            "actual": self.actual,
            "screenshot": self.screenshot.to_dict() if self.screenshot else None,
            "message": self.message,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "metadata": self.metadata,
        }


class VisualVerifier:
    """
    Visual verification using headless browser (Playwright).

    Provides screenshot capture and UI verification capabilities for
    Meta Agent task verification.
    """

    # Default viewport size
    DEFAULT_VIEWPORT_WIDTH = 1280
    DEFAULT_VIEWPORT_HEIGHT = 720

    # Default timeout for page operations (milliseconds)
    DEFAULT_TIMEOUT_MS = 30000

    # Default wait time after navigation (milliseconds)
    DEFAULT_NAVIGATION_WAIT_MS = 1000

    def __init__(
        self,
        headless: bool = True,
        viewport_width: int = DEFAULT_VIEWPORT_WIDTH,
        viewport_height: int = DEFAULT_VIEWPORT_HEIGHT,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ):
        """
        Initialize the VisualVerifier.

        Args:
            headless: Run browser in headless mode (default: True)
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            timeout_ms: Default timeout for page operations
        """
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout_ms = timeout_ms

        self._browser = None
        self._playwright = None
        self._is_initialized = False

        logger.info(
            "[VisualVerifier] Initialized with headless=%s, viewport=%dx%d",
            headless, viewport_width, viewport_height
        )

    async def _ensure_browser(self) -> None:
        """Ensure browser is launched and ready"""
        if self._is_initialized and self._browser:
            return

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
            self._is_initialized = True

            logger.info("[VisualVerifier] Browser launched successfully")

        except ImportError:
            logger.error(
                "[VisualVerifier] Playwright not installed. "
                "Install with: pip install playwright && playwright install chromium"
            )
            raise
        except Exception as e:
            logger.error("[VisualVerifier] Failed to launch browser: %s", e)
            raise

    async def close(self) -> None:
        """Close browser and cleanup resources"""
        if self._browser:
            try:
                await self._browser.close()
                logger.info("[VisualVerifier] Browser closed")
            except Exception as e:
                logger.warning("[VisualVerifier] Error closing browser: %s", e)
            finally:
                self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning("[VisualVerifier] Error stopping playwright: %s", e)
            finally:
                self._playwright = None

        self._is_initialized = False

    async def capture_screenshot(
        self,
        url: str,
        selector: Optional[str] = None,
        full_page: bool = False,
        wait_for_selector: Optional[str] = None,
        wait_timeout_ms: Optional[int] = None,
    ) -> ScreenshotResult:
        """
        Capture screenshot of a page or element.

        Args:
            url: URL to navigate to
            selector: CSS selector for specific element (optional)
            full_page: Capture full page screenshot
            wait_for_selector: Wait for this selector before screenshot
            wait_timeout_ms: Timeout for waiting (default: self.timeout_ms)

        Returns:
            ScreenshotResult with screenshot data
        """
        try:
            await self._ensure_browser()

            # Use async with to ensure context is always closed even on exceptions
            async with await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            ) as context:
                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, timeout=self.timeout_ms)

                # Wait for navigation to settle
                await asyncio.sleep(self.DEFAULT_NAVIGATION_WAIT_MS / 1000)

                # Wait for specific selector if requested
                if wait_for_selector:
                    timeout = wait_timeout_ms or self.timeout_ms
                    await page.wait_for_selector(wait_for_selector, timeout=timeout)

                # Capture screenshot
                if selector:
                    element = await page.query_selector(selector)
                    if element:
                        screenshot_bytes = await element.screenshot()
                        box = await element.bounding_box()
                        width = int(box["width"]) if box else 0
                        height = int(box["height"]) if box else 0
                    else:
                        return ScreenshotResult(
                            success=False,
                            url=url,
                            selector=selector,
                            error=f"Element not found: {selector}",
                        )
                else:
                    screenshot_bytes = await page.screenshot(full_page=full_page)
                    width = self.viewport_width
                    height = self.viewport_height if not full_page else 0

                return ScreenshotResult(
                    success=True,
                    url=url,
                    screenshot_bytes=screenshot_bytes,
                    selector=selector,
                    width=width,
                    height=height,
                    captured_at=datetime.now(),
                )

        except Exception as e:
            logger.error(
                "[VisualVerifier] Screenshot capture failed for %s: %s",
                url, e
            )
            return ScreenshotResult(
                success=False,
                url=url,
                selector=selector,
                error=str(e),
            )

    async def verify_element_exists(
        self,
        url: str,
        selector: str,
        timeout_ms: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify that an element exists on the page.

        Args:
            url: URL to navigate to
            selector: CSS selector for the element
            timeout_ms: Timeout for waiting

        Returns:
            VerificationResult indicating pass/fail
        """
        try:
            await self._ensure_browser()

            # Use async with to ensure context is always closed even on exceptions
            async with await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            ) as context:
                page = await context.new_page()

                await page.goto(url, timeout=self.timeout_ms)
                await asyncio.sleep(self.DEFAULT_NAVIGATION_WAIT_MS / 1000)

                timeout = timeout_ms or self.timeout_ms
                element = await page.wait_for_selector(
                    selector, timeout=timeout, state="attached"
                )

                exists = element is not None

                return VerificationResult(
                    status=VerificationStatus.PASSED if exists else VerificationStatus.FAILED,
                    check_type="element_exists",
                    passed=exists,
                    url=url,
                    selector=selector,
                    expected=True,
                    actual=exists,
                    message=f"Element {'found' if exists else 'not found'}: {selector}",
                    verified_at=datetime.now(),
                )

        except Exception as e:
            logger.error(
                "[VisualVerifier] Element existence check failed for %s: %s",
                selector, e
            )
            return VerificationResult(
                status=VerificationStatus.ERROR,
                check_type="element_exists",
                passed=False,
                url=url,
                selector=selector,
                expected=True,
                actual=False,
                message=f"Error checking element: {e}",
                verified_at=datetime.now(),
            )

    async def verify_element_visible(
        self,
        url: str,
        selector: str,
        timeout_ms: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify that an element is visible on the page.

        Args:
            url: URL to navigate to
            selector: CSS selector for the element
            timeout_ms: Timeout for waiting

        Returns:
            VerificationResult indicating pass/fail
        """
        try:
            await self._ensure_browser()

            # Use async with to ensure context is always closed even on exceptions
            async with await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            ) as context:
                page = await context.new_page()

                await page.goto(url, timeout=self.timeout_ms)
                await asyncio.sleep(self.DEFAULT_NAVIGATION_WAIT_MS / 1000)

                timeout = timeout_ms or self.timeout_ms
                try:
                    await page.wait_for_selector(
                        selector, timeout=timeout, state="visible"
                    )
                    is_visible = True
                except Exception:
                    is_visible = False

                return VerificationResult(
                    status=VerificationStatus.PASSED if is_visible else VerificationStatus.FAILED,
                    check_type="element_visible",
                    passed=is_visible,
                    url=url,
                    selector=selector,
                    expected=True,
                    actual=is_visible,
                    message=f"Element {'visible' if is_visible else 'not visible'}: {selector}",
                    verified_at=datetime.now(),
                )

        except Exception as e:
            logger.error(
                "[VisualVerifier] Element visibility check failed for %s: %s",
                selector, e
            )
            return VerificationResult(
                status=VerificationStatus.ERROR,
                check_type="element_visible",
                passed=False,
                url=url,
                selector=selector,
                expected=True,
                actual=False,
                message=f"Error checking visibility: {e}",
                verified_at=datetime.now(),
            )

    async def verify_element_text(
        self,
        url: str,
        selector: str,
        expected_text: str,
        exact_match: bool = False,
        timeout_ms: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify that an element contains expected text.

        Args:
            url: URL to navigate to
            selector: CSS selector for the element
            expected_text: Text to look for
            exact_match: Require exact match (default: contains)
            timeout_ms: Timeout for waiting

        Returns:
            VerificationResult indicating pass/fail
        """
        try:
            await self._ensure_browser()

            # Use async with to ensure context is always closed even on exceptions
            async with await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            ) as context:
                page = await context.new_page()

                await page.goto(url, timeout=self.timeout_ms)
                await asyncio.sleep(self.DEFAULT_NAVIGATION_WAIT_MS / 1000)

                timeout = timeout_ms or self.timeout_ms
                element = await page.wait_for_selector(selector, timeout=timeout)

                if element:
                    actual_text = await element.text_content() or ""
                    if exact_match:
                        passed = actual_text.strip() == expected_text.strip()
                    else:
                        passed = expected_text in actual_text
                else:
                    actual_text = ""
                    passed = False

                return VerificationResult(
                    status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
                    check_type="element_text",
                    passed=passed,
                    url=url,
                    selector=selector,
                    expected=expected_text,
                    actual=actual_text,
                    message=f"Text {'matches' if passed else 'does not match'}",
                    verified_at=datetime.now(),
                )

        except Exception as e:
            logger.error(
                "[VisualVerifier] Element text check failed for %s: %s",
                selector, e
            )
            return VerificationResult(
                status=VerificationStatus.ERROR,
                check_type="element_text",
                passed=False,
                url=url,
                selector=selector,
                expected=expected_text,
                actual=None,
                message=f"Error checking text: {e}",
                verified_at=datetime.now(),
            )

    async def verify_element_centered(
        self,
        url: str,
        selector: str,
        tolerance_px: int = 10,
        timeout_ms: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify if an element is horizontally centered in the viewport.

        Args:
            url: URL to navigate to
            selector: CSS selector for the element
            tolerance_px: Allowed deviation from center in pixels
            timeout_ms: Timeout for waiting

        Returns:
            VerificationResult indicating pass/fail
        """
        try:
            await self._ensure_browser()

            # Use async with to ensure context is always closed even on exceptions
            async with await self._browser.new_context(
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                }
            ) as context:
                page = await context.new_page()

                await page.goto(url, timeout=self.timeout_ms)
                await asyncio.sleep(self.DEFAULT_NAVIGATION_WAIT_MS / 1000)

                timeout = timeout_ms or self.timeout_ms
                element = await page.wait_for_selector(selector, timeout=timeout)

                if element:
                    box = await element.bounding_box()
                    if box:
                        element_center_x = box["x"] + box["width"] / 2
                        viewport_center_x = self.viewport_width / 2
                        offset = abs(element_center_x - viewport_center_x)
                        is_centered = offset <= tolerance_px

                        return VerificationResult(
                            status=VerificationStatus.PASSED if is_centered else VerificationStatus.FAILED,
                            check_type="element_centered",
                            passed=is_centered,
                            url=url,
                            selector=selector,
                            expected=f"centered (tolerance: {tolerance_px}px)",
                            actual=f"offset: {offset:.1f}px",
                            message=f"Element {'is' if is_centered else 'is not'} centered (offset: {offset:.1f}px)",
                            verified_at=datetime.now(),
                            metadata={
                                "element_center_x": element_center_x,
                                "viewport_center_x": viewport_center_x,
                                "offset_px": offset,
                                "tolerance_px": tolerance_px,
                            },
                        )

                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    check_type="element_centered",
                    passed=False,
                    url=url,
                    selector=selector,
                    message=f"Element not found or has no bounding box: {selector}",
                    verified_at=datetime.now(),
                )

        except Exception as e:
            logger.error(
                "[VisualVerifier] Element centering check failed for %s: %s",
                selector, e
            )
            return VerificationResult(
                status=VerificationStatus.ERROR,
                check_type="element_centered",
                passed=False,
                url=url,
                selector=selector,
                message=f"Error checking centering: {e}",
                verified_at=datetime.now(),
            )

    async def run_verification_suite(
        self,
        url: str,
        checks: List[Dict[str, Any]],
    ) -> List[VerificationResult]:
        """
        Run a suite of verification checks.

        Args:
            url: URL to verify
            checks: List of check configurations, each with:
                - type: "exists", "visible", "text", "centered"
                - selector: CSS selector
                - expected: Expected value (for text checks)
                - options: Additional options

        Returns:
            List of VerificationResult for each check
        """
        results = []

        for check in checks:
            check_type = check.get("type", "exists")
            selector = check.get("selector", "")
            options = check.get("options", {})

            if check_type == "exists":
                result = await self.verify_element_exists(url, selector)
            elif check_type == "visible":
                result = await self.verify_element_visible(url, selector)
            elif check_type == "text":
                expected = check.get("expected", "")
                exact = options.get("exact_match", False)
                result = await self.verify_element_text(
                    url, selector, expected, exact_match=exact
                )
            elif check_type == "centered":
                tolerance = options.get("tolerance_px", 10)
                result = await self.verify_element_centered(
                    url, selector, tolerance_px=tolerance
                )
            else:
                result = VerificationResult(
                    status=VerificationStatus.SKIPPED,
                    check_type=check_type,
                    passed=False,
                    url=url,
                    selector=selector,
                    message=f"Unknown check type: {check_type}",
                    verified_at=datetime.now(),
                )

            results.append(result)

        return results


async def create_visual_verifier(
    headless: bool = True,
    viewport_width: int = VisualVerifier.DEFAULT_VIEWPORT_WIDTH,
    viewport_height: int = VisualVerifier.DEFAULT_VIEWPORT_HEIGHT,
) -> VisualVerifier:
    """
    Factory function to create and initialize a VisualVerifier.

    Args:
        headless: Run browser in headless mode
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height

    Returns:
        Initialized VisualVerifier instance
    """
    verifier = VisualVerifier(
        headless=headless,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )
    return verifier
