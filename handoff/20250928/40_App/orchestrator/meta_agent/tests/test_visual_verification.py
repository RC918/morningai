"""
Tests for Visual Verifier Module

Issue: #2073 - add Visual Verification infrastructure with headless browser

Test coverage:
    - Screenshot capture functionality
    - Element existence verification
    - Element visibility verification
    - Element text verification
    - Element centering verification
    - Headless browser unavailable fallback
    - Integration with AutonomousExecutor
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from orchestrator.meta_agent.visual_verifier import (
    VisualVerifier,
    VerificationStatus,
    ScreenshotResult,
    VerificationResult,
    create_visual_verifier,
)


class TestScreenshotResult:
    """Tests for ScreenshotResult dataclass"""

    def test_screenshot_result_success(self):
        """Test successful screenshot result"""
        result = ScreenshotResult(
            success=True,
            url="https://example.com",
            screenshot_bytes=b"fake_image_data",
            width=1280,
            height=720,
            captured_at=datetime.now(),
        )

        assert result.success is True
        assert result.url == "https://example.com"
        assert result.screenshot_bytes == b"fake_image_data"
        assert result.width == 1280
        assert result.height == 720
        assert result.error is None

    def test_screenshot_result_failure(self):
        """Test failed screenshot result"""
        result = ScreenshotResult(
            success=False,
            url="https://example.com",
            error="Element not found",
        )

        assert result.success is False
        assert result.error == "Element not found"

    def test_screenshot_result_to_dict(self):
        """Test screenshot result serialization"""
        captured_at = datetime.now()
        result = ScreenshotResult(
            success=True,
            url="https://example.com",
            selector="#main",
            width=800,
            height=600,
            captured_at=captured_at,
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["url"] == "https://example.com"
        assert data["selector"] == "#main"
        assert data["width"] == 800
        assert data["height"] == 600
        assert data["captured_at"] == captured_at.isoformat()


class TestVerificationResult:
    """Tests for VerificationResult dataclass"""

    def test_verification_result_passed(self):
        """Test passed verification result"""
        result = VerificationResult(
            status=VerificationStatus.PASSED,
            check_type="element_exists",
            passed=True,
            url="https://example.com",
            selector="#button",
            message="Element found",
            verified_at=datetime.now(),
        )

        assert result.status == VerificationStatus.PASSED
        assert result.passed is True
        assert result.check_type == "element_exists"

    def test_verification_result_failed(self):
        """Test failed verification result"""
        result = VerificationResult(
            status=VerificationStatus.FAILED,
            check_type="element_text",
            passed=False,
            url="https://example.com",
            selector="#title",
            expected="Hello",
            actual="Goodbye",
            message="Text does not match",
        )

        assert result.status == VerificationStatus.FAILED
        assert result.passed is False
        assert result.expected == "Hello"
        assert result.actual == "Goodbye"

    def test_verification_result_to_dict(self):
        """Test verification result serialization"""
        verified_at = datetime.now()
        result = VerificationResult(
            status=VerificationStatus.PASSED,
            check_type="element_visible",
            passed=True,
            url="https://example.com",
            selector="#nav",
            verified_at=verified_at,
        )

        data = result.to_dict()

        assert data["status"] == "passed"
        assert data["check_type"] == "element_visible"
        assert data["passed"] is True
        assert data["verified_at"] == verified_at.isoformat()


class TestVisualVerifier:
    """Tests for VisualVerifier class"""

    def test_init_default_values(self):
        """Test VisualVerifier initialization with defaults"""
        verifier = VisualVerifier()

        assert verifier.headless is True
        assert verifier.viewport_width == 1280
        assert verifier.viewport_height == 720
        assert verifier.timeout_ms == 30000
        assert verifier._is_initialized is False

    def test_init_custom_values(self):
        """Test VisualVerifier initialization with custom values"""
        verifier = VisualVerifier(
            headless=False,
            viewport_width=1920,
            viewport_height=1080,
            timeout_ms=60000,
        )

        assert verifier.headless is False
        assert verifier.viewport_width == 1920
        assert verifier.viewport_height == 1080
        assert verifier.timeout_ms == 60000

    @pytest.mark.asyncio
    async def test_capture_screenshot_success(self):
        """Test successful screenshot capture with mocked browser"""
        verifier = VisualVerifier()

        # Mock playwright components
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"screenshot_data")

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.capture_screenshot("https://example.com")

        assert result.success is True
        assert result.url == "https://example.com"
        assert result.screenshot_bytes == b"screenshot_data"

    @pytest.mark.asyncio
    async def test_capture_screenshot_with_selector(self):
        """Test screenshot capture of specific element"""
        verifier = VisualVerifier()

        # Mock element with bounding box
        mock_element = AsyncMock()
        mock_element.screenshot = AsyncMock(return_value=b"element_screenshot")
        mock_element.bounding_box = AsyncMock(
            return_value={"x": 100, "y": 100, "width": 200, "height": 100}
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.capture_screenshot(
            "https://example.com",
            selector="#main-content"
        )

        assert result.success is True
        assert result.selector == "#main-content"
        assert result.width == 200
        assert result.height == 100

    @pytest.mark.asyncio
    async def test_capture_screenshot_element_not_found(self):
        """Test screenshot capture when element not found"""
        verifier = VisualVerifier()

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.capture_screenshot(
            "https://example.com",
            selector="#nonexistent"
        )

        assert result.success is False
        assert "Element not found" in result.error

    @pytest.mark.asyncio
    async def test_verify_element_exists_found(self):
        """Test element existence verification when element exists"""
        verifier = VisualVerifier()

        mock_element = AsyncMock()

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.verify_element_exists(
            "https://example.com",
            "#submit-button"
        )

        assert result.status == VerificationStatus.PASSED
        assert result.passed is True
        assert result.check_type == "element_exists"

    @pytest.mark.asyncio
    async def test_verify_element_text_matches(self):
        """Test element text verification when text matches"""
        verifier = VisualVerifier()

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Welcome to MorningAI")

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.verify_element_text(
            "https://example.com",
            "#title",
            "Welcome"
        )

        assert result.status == VerificationStatus.PASSED
        assert result.passed is True
        assert "Welcome to MorningAI" in result.actual

    @pytest.mark.asyncio
    async def test_verify_element_text_no_match(self):
        """Test element text verification when text doesn't match"""
        verifier = VisualVerifier()

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Goodbye")

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.verify_element_text(
            "https://example.com",
            "#title",
            "Hello"
        )

        assert result.status == VerificationStatus.FAILED
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_verify_element_centered_is_centered(self):
        """Test element centering verification when element is centered"""
        verifier = VisualVerifier(viewport_width=1280)

        mock_element = AsyncMock()
        # Element centered at viewport center (640px)
        mock_element.bounding_box = AsyncMock(
            return_value={"x": 540, "y": 100, "width": 200, "height": 50}
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.verify_element_centered(
            "https://example.com",
            "#centered-element"
        )

        assert result.status == VerificationStatus.PASSED
        assert result.passed is True
        assert result.check_type == "element_centered"

    @pytest.mark.asyncio
    async def test_verify_element_centered_not_centered(self):
        """Test element centering verification when element is not centered"""
        verifier = VisualVerifier(viewport_width=1280)

        mock_element = AsyncMock()
        # Element far from center
        mock_element.bounding_box = AsyncMock(
            return_value={"x": 50, "y": 100, "width": 100, "height": 50}
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.verify_element_centered(
            "https://example.com",
            "#left-element"
        )

        assert result.status == VerificationStatus.FAILED
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_run_verification_suite(self):
        """Test running a suite of verification checks"""
        verifier = VisualVerifier()

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Test Content")
        mock_element.bounding_box = AsyncMock(
            return_value={"x": 540, "y": 100, "width": 200, "height": 50}
        )

        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        # Directly set internal state to bypass _ensure_browser
        verifier._browser = mock_browser
        verifier._is_initialized = True

        checks = [
            {"type": "exists", "selector": "#header"},
            {"type": "text", "selector": "#content", "expected": "Test"},
        ]

        results = await verifier.run_verification_suite(
            "https://example.com",
            checks
        )

        assert len(results) == 2
        assert results[0].check_type == "element_exists"
        assert results[1].check_type == "element_text"

    @pytest.mark.asyncio
    async def test_capture_screenshot_browser_error(self):
        """Test screenshot capture when browser throws error"""
        verifier = VisualVerifier()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(side_effect=Exception("Browser error"))

        # Directly set internal state
        verifier._browser = mock_browser
        verifier._is_initialized = True

        result = await verifier.capture_screenshot("https://example.com")

        assert result.success is False
        assert "Browser error" in result.error

    @pytest.mark.asyncio
    async def test_close_cleanup(self):
        """Test that close properly cleans up resources"""
        verifier = VisualVerifier()

        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()

        mock_playwright = AsyncMock()
        mock_playwright.stop = AsyncMock()

        verifier._browser = mock_browser
        verifier._playwright = mock_playwright
        verifier._is_initialized = True

        await verifier.close()

        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert verifier._browser is None
        assert verifier._playwright is None
        assert verifier._is_initialized is False


class TestCreateVisualVerifier:
    """Tests for create_visual_verifier factory function"""

    @pytest.mark.asyncio
    async def test_create_visual_verifier_defaults(self):
        """Test factory function with default values"""
        verifier = await create_visual_verifier()

        assert verifier.headless is True
        assert verifier.viewport_width == 1280
        assert verifier.viewport_height == 720

    @pytest.mark.asyncio
    async def test_create_visual_verifier_custom(self):
        """Test factory function with custom values"""
        verifier = await create_visual_verifier(
            headless=False,
            viewport_width=1920,
            viewport_height=1080,
        )

        assert verifier.headless is False
        assert verifier.viewport_width == 1920
        assert verifier.viewport_height == 1080


class TestAutonomousExecutorVerificationIntegration:
    """Tests for VisualVerifier integration with AutonomousExecutor"""

    @pytest.mark.asyncio
    async def test_handle_verification_without_visual_config(self):
        """Test verification handler without visual verification config"""
        from orchestrator.meta_agent.autonomous_executor import AutonomousExecutor
        from orchestrator.meta_agent.task_planner import SubTask, SubTaskType

        executor = AutonomousExecutor()

        task = SubTask(
            task_id="test-task-1",
            task_type=SubTaskType.VERIFICATION,
            description="Verify functionality",
            inputs={},
        )

        result = await executor._handle_verification(task)

        assert result["verification_passed"] is True
        assert "Functionality" in result["checks_performed"]
        assert "No regressions" in result["checks_performed"]
        assert result["visual_verification_results"] == []

    @pytest.mark.asyncio
    async def test_handle_verification_with_visual_config(self):
        """Test verification handler with visual verification config"""
        from orchestrator.meta_agent.autonomous_executor import AutonomousExecutor
        from orchestrator.meta_agent.task_planner import SubTask, SubTaskType

        executor = AutonomousExecutor()

        task = SubTask(
            task_id="test-task-2",
            task_type=SubTaskType.VERIFICATION,
            description="Verify UI",
            inputs={
                "visual_verification": {
                    "url": "https://example.com",
                    "screenshot": True,
                    "checks": [
                        {"type": "exists", "selector": "#header"},
                    ],
                }
            },
        )

        # Mock the VisualVerifier
        mock_screenshot = ScreenshotResult(
            success=True,
            url="https://example.com",
            screenshot_bytes=b"fake_data",
            width=1280,
            height=720,
        )

        mock_verification = VerificationResult(
            status=VerificationStatus.PASSED,
            check_type="element_exists",
            passed=True,
            url="https://example.com",
            selector="#header",
        )

        with patch(
            "orchestrator.meta_agent.autonomous_executor.VisualVerifier"
        ) as MockVerifier:
            mock_instance = AsyncMock()
            mock_instance.capture_screenshot = AsyncMock(return_value=mock_screenshot)
            mock_instance.run_verification_suite = AsyncMock(
                return_value=[mock_verification]
            )
            mock_instance.close = AsyncMock()
            MockVerifier.return_value = mock_instance

            result = await executor._handle_verification(task)

        assert result["verification_passed"] is True
        assert "Screenshot capture" in result["checks_performed"]
        assert len(result["visual_verification_results"]) == 1
        assert result["screenshot"] is not None

    @pytest.mark.asyncio
    async def test_handle_verification_playwright_unavailable(self):
        """Test verification handler when Playwright is unavailable"""
        from orchestrator.meta_agent.autonomous_executor import AutonomousExecutor
        from orchestrator.meta_agent.task_planner import SubTask, SubTaskType

        executor = AutonomousExecutor()

        task = SubTask(
            task_id="test-task-3",
            task_type=SubTaskType.VERIFICATION,
            description="Verify UI",
            inputs={
                "visual_verification": {
                    "url": "https://example.com",
                    "screenshot": True,
                }
            },
        )

        with patch(
            "orchestrator.meta_agent.autonomous_executor.VisualVerifier",
            side_effect=ImportError("No module named 'playwright'")
        ):
            result = await executor._handle_verification(task)

        # Should fall back to basic verification
        assert result["verification_passed"] is True
        assert "Fallback: Playwright unavailable" in result["checks_performed"]
        assert "Functionality" in result["checks_performed"]
