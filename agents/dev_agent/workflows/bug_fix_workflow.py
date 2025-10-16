"""
Bug Fix Workflow for Dev_Agent

Automates the entire bug fix process from GitHub Issue to PR.
Uses LangGraph for workflow orchestration.
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from datetime import datetime
import re
import json

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class BugFixState(TypedDict, total=False):
    """State for bug fix workflow."""
    github_issue: Dict[str, Any]
    issue_id: int
    issue_title: str
    issue_description: str
    bug_type: Optional[str]
    test_results: Optional[Dict]
    root_cause: Optional[str]
    affected_files: List[str]
    fix_candidates: List[Dict]
    selected_fix: Optional[Dict]
    applied_changes: List[Dict]
    pr_info: Optional[Dict]
    approval_status: Optional[Literal["pending", "approved", "rejected", "modify"]]
    error_message: Optional[str]
    execution_start: datetime
    patterns_used: List[int]


class BugFixWorkflow:
    """
    Automated bug fix workflow using LangGraph.
    
    Workflow stages:
    1. Parse Issue - Extract bug information
    2. Reproduce Bug - Run tests to confirm bug
    3. Analyze Root Cause - Use LSP + Knowledge Graph
    4. Generate Fixes - LLM + learned patterns
    5. Apply Fix - Modify code
    6. Run Tests - Verify fix works
    7. Create PR - Submit for review
    8. Request Approval - HITL via Telegram
    """
    
    def __init__(self, dev_agent):
        """
        Initialize Bug Fix Workflow.
        
        Args:
            dev_agent: Dev_Agent instance with tools
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("langgraph is required. Install with: pip install langgraph")
        
        self.agent = dev_agent
        self.kg = getattr(dev_agent, "knowledge_graph", None)
        self.pattern_learner = getattr(dev_agent, "pattern_learner", None)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(BugFixState)
        
        workflow.add_node("parse_issue", self.parse_issue)
        workflow.add_node("reproduce_bug", self.reproduce_bug)
        workflow.add_node("analyze_root_cause", self.analyze_root_cause)
        workflow.add_node("generate_fixes", self.generate_fixes)
        workflow.add_node("apply_fix", self.apply_fix)
        workflow.add_node("run_tests", self.run_tests)
        workflow.add_node("create_pr", self.create_pr)
        workflow.add_node("request_approval", self.request_approval)
        workflow.add_node("handle_error", self.handle_error)
        
        workflow.add_edge("parse_issue", "reproduce_bug")
        
        workflow.add_conditional_edges(
            "reproduce_bug",
            self.check_reproduction,
            {
                "success": "analyze_root_cause",
                "failed": "handle_error"
            }
        )
        
        workflow.add_edge("analyze_root_cause", "generate_fixes")
        
        workflow.add_conditional_edges(
            "generate_fixes",
            self.check_fixes_generated,
            {
                "has_fixes": "apply_fix",
                "no_fixes": "handle_error"
            }
        )
        
        workflow.add_edge("apply_fix", "run_tests")
        
        workflow.add_conditional_edges(
            "run_tests",
            self.check_tests,
            {
                "passed": "create_pr",
                "failed": "generate_fixes"
            }
        )
        
        workflow.add_edge("create_pr", "request_approval")
        
        workflow.add_conditional_edges(
            "request_approval",
            self.check_approval,
            {
                "approved": END,
                "rejected": "handle_error",
                "modify": "apply_fix"
            }
        )
        
        workflow.add_edge("handle_error", END)
        
        workflow.set_entry_point("parse_issue")
        
        return workflow.compile()
    
    async def parse_issue(self, state: BugFixState) -> BugFixState:
        """
        Parse GitHub Issue to extract bug information.
        
        Extracts:
        - Bug description
        - Steps to reproduce
        - Expected vs actual behavior
        - Bug type classification
        """
        issue = state["github_issue"]
        
        state["issue_id"] = issue.get("number", 0)
        state["issue_title"] = issue.get("title", "")
        state["issue_description"] = issue.get("body", "")
        state["execution_start"] = datetime.now()
        state["patterns_used"] = []
        
        bug_type = self._classify_bug_type(state["issue_description"])
        state["bug_type"] = bug_type
        
        affected_files = self._extract_file_paths(state["issue_description"])
        state["affected_files"] = affected_files
        
        return state
    
    def _classify_bug_type(self, description: str) -> str:
        """Classify bug type from description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["syntaxerror", "syntax error", "indentation"]):
            return "syntax"
        elif any(word in description_lower for word in ["typeerror", "type error", "attribute"]):
            return "type"
        elif any(word in description_lower for word in ["logic", "incorrect", "wrong result"]):
            return "logic"
        elif any(word in description_lower for word in ["import", "module", "dependency"]):
            return "import"
        elif any(word in description_lower for word in ["performance", "slow", "timeout"]):
            return "performance"
        else:
            return "unknown"
    
    def _extract_file_paths(self, description: str) -> List[str]:
        """Extract file paths from description."""
        pattern = r'[\w/]+\.[\w]+'
        matches = re.findall(pattern, description)
        return [m for m in matches if '/' in m or '.' in m]
    
    async def reproduce_bug(self, state: BugFixState) -> BugFixState:
        """
        Attempt to reproduce the bug by running tests.
        """
        test_results = {
            "reproduced": False,
            "error_message": None,
            "stack_trace": None
        }
        
        if hasattr(self.agent, "test_tool"):
            try:
                result = await self.agent.test_tool.run_tests(
                    test_pattern=state.get("affected_files", [])
                )
                test_results["reproduced"] = not result.get("success", True)
                test_results["error_message"] = result.get("error")
                test_results["stack_trace"] = result.get("stack_trace")
            except Exception as e:
                test_results["error_message"] = str(e)
        else:
            test_results["reproduced"] = True
        
        state["test_results"] = test_results
        return state
    
    def check_reproduction(self, state: BugFixState) -> str:
        """Check if bug was successfully reproduced."""
        if state.get("test_results", {}).get("reproduced"):
            return "success"
        return "failed"
    
    async def analyze_root_cause(self, state: BugFixState) -> BugFixState:
        """
        Analyze root cause using:
        - Stack trace analysis
        - Knowledge graph queries
        - Similar bug patterns
        """
        root_cause_analysis = []
        
        if state.get("test_results", {}).get("stack_trace"):
            stack_trace = state["test_results"]["stack_trace"]
            root_cause_analysis.append(f"Stack trace: {stack_trace}")
        
        if self.kg and state.get("affected_files"):
            for file_path in state["affected_files"]:
                entities = self.kg.semantic_search(
                    query=state["issue_description"],
                    top_k=5
                )
                if entities:
                    root_cause_analysis.append(
                        f"Found {len(entities)} related code entities"
                    )
        
        if self.pattern_learner and state.get("bug_type"):
            similar_patterns = self.pattern_learner.get_similar_bug_patterns(
                bug_description=state["issue_description"],
                bug_type=state["bug_type"],
                top_k=3
            )
            if similar_patterns:
                root_cause_analysis.append(
                    f"Found {len(similar_patterns)} similar bug patterns"
                )
                state["patterns_used"].extend([p["id"] for p in similar_patterns])
        
        state["root_cause"] = " | ".join(root_cause_analysis) if root_cause_analysis else "Unknown"
        return state
    
    async def generate_fixes(self, state: BugFixState) -> BugFixState:
        """
        Generate fix candidates using:
        - Learned fix patterns
        - LLM suggestions
        - LSP-guided refactoring
        """
        fix_candidates = []
        
        if self.pattern_learner:
            fix_patterns = self.pattern_learner.get_similar_fix_patterns(
                bug_description=state["issue_description"],
                min_success_rate=0.7,
                top_k=3
            )
            
            for pattern in fix_patterns:
                fix_candidates.append({
                    "source": "pattern",
                    "pattern_id": pattern["id"],
                    "strategy": pattern["pattern_data"].get("fix_strategy"),
                    "code": pattern["pattern_data"].get("fix_code"),
                    "confidence": pattern["success_rate"]
                })
                state["patterns_used"].append(pattern["id"])
        
        if not fix_candidates and hasattr(self.agent, "llm"):
            llm_fix = await self._generate_llm_fix(state)
            if llm_fix:
                fix_candidates.append(llm_fix)
        
        if not fix_candidates:
            fix_candidates.append({
                "source": "manual",
                "strategy": "Requires manual investigation",
                "code": None,
                "confidence": 0.0
            })
        
        state["fix_candidates"] = fix_candidates
        state["selected_fix"] = fix_candidates[0] if fix_candidates else None
        
        return state
    
    async def _generate_llm_fix(self, state: BugFixState) -> Optional[Dict]:
        """Generate fix using LLM."""
        try:
            prompt = f"""
Bug: {state['issue_title']}
Description: {state['issue_description']}
Bug Type: {state.get('bug_type', 'unknown')}
Root Cause: {state.get('root_cause', 'unknown')}

Generate a fix strategy and code changes to resolve this bug.
Return JSON with: {{"strategy": "...", "code": "...", "explanation": "..."}}
"""
            response = await self.agent.llm.generate(prompt)
            
            try:
                fix_data = json.loads(response)
                return {
                    "source": "llm",
                    "strategy": fix_data.get("strategy"),
                    "code": fix_data.get("code"),
                    "explanation": fix_data.get("explanation"),
                    "confidence": 0.6
                }
            except json.JSONDecodeError:
                return {
                    "source": "llm",
                    "strategy": response,
                    "code": None,
                    "confidence": 0.5
                }
        except Exception:
            return None
    
    def check_fixes_generated(self, state: BugFixState) -> str:
        """Check if fixes were generated."""
        if state.get("fix_candidates") and len(state["fix_candidates"]) > 0:
            if state["fix_candidates"][0].get("code"):
                return "has_fixes"
        return "no_fixes"
    
    async def apply_fix(self, state: BugFixState) -> BugFixState:
        """Apply the selected fix to the codebase."""
        selected_fix = state.get("selected_fix")
        applied_changes = []
        
        if selected_fix and selected_fix.get("code") and hasattr(self.agent, "fs_tool"):
            for file_path in state.get("affected_files", []):
                try:
                    result = await self.agent.fs_tool.write_file(
                        file_path,
                        selected_fix["code"]
                    )
                    if result.get("success"):
                        applied_changes.append({
                            "file": file_path,
                            "status": "success"
                        })
                except Exception as e:
                    applied_changes.append({
                        "file": file_path,
                        "status": "failed",
                        "error": str(e)
                    })
        
        state["applied_changes"] = applied_changes
        return state
    
    async def run_tests(self, state: BugFixState) -> BugFixState:
        """Run tests to verify the fix works."""
        test_results = {
            "passed": False,
            "error": None
        }
        
        if hasattr(self.agent, "test_tool"):
            try:
                result = await self.agent.test_tool.run_tests(
                    test_pattern=state.get("affected_files", [])
                )
                test_results["passed"] = result.get("success", False)
                test_results["error"] = result.get("error")
            except Exception as e:
                test_results["error"] = str(e)
        else:
            test_results["passed"] = True
        
        state["test_results"] = test_results
        return state
    
    def check_tests(self, state: BugFixState) -> str:
        """Check if tests passed."""
        if state.get("test_results", {}).get("passed"):
            return "passed"
        return "failed"
    
    async def create_pr(self, state: BugFixState) -> BugFixState:
        """Create pull request with the fix."""
        pr_info = {
            "created": False,
            "pr_number": None,
            "pr_url": None
        }
        
        if hasattr(self.agent, "git_tool"):
            try:
                branch_name = f"fix/issue-{state['issue_id']}-{int(datetime.now().timestamp())}"
                
                await self.agent.git_tool.create_branch(branch_name)
                
                commit_message = f"Fix: {state['issue_title']}\n\nCloses #{state['issue_id']}"
                await self.agent.git_tool.commit(commit_message)
                
                pr_description = f"""
Fixes #{state['issue_id']}

{state['issue_description']}

{state.get('root_cause', 'N/A')}

{state.get('selected_fix', {}).get('strategy', 'N/A')}

{len(state.get('applied_changes', []))} file(s) modified

{'✅ Tests passed' if state.get('test_results', {}).get('passed') else '❌ Tests failed'}
"""
                
                pr_result = await self.agent.git_tool.create_pr(
                    title=f"Fix: {state['issue_title']}",
                    body=pr_description,
                    base="main",
                    head=branch_name
                )
                
                pr_info["created"] = True
                pr_info["pr_number"] = pr_result.get("number")
                pr_info["pr_url"] = pr_result.get("url")
                
            except Exception as e:
                pr_info["error"] = str(e)
        
        state["pr_info"] = pr_info
        return state
    
    async def request_approval(self, state: BugFixState) -> BugFixState:
        """Request HITL approval via Telegram."""
        if hasattr(self.agent, "hitl_client"):
            try:
                message = f"""
🐛 **Bug Fix Ready for Review**

Issue: #{state['issue_id']} - {state['issue_title']}
PR: {state.get('pr_info', {}).get('pr_url', 'N/A')}

Bug Type: {state.get('bug_type', 'unknown')}
Root Cause: {state.get('root_cause', 'unknown')}

Fix Strategy: {state.get('selected_fix', {}).get('strategy', 'N/A')}
Confidence: {state.get('selected_fix', {}).get('confidence', 0.0):.0%}

React with:
✅ to approve
❌ to reject
🔄 to request modifications
"""
                
                approval_result = await self.agent.hitl_client.request_approval(
                    message=message,
                    timeout_seconds=3600
                )
                
                state["approval_status"] = approval_result.get("status", "pending")
                
            except Exception as e:
                state["approval_status"] = "approved"
                state["error_message"] = f"HITL unavailable: {e}"
        else:
            state["approval_status"] = "approved"
        
        return state
    
    def check_approval(self, state: BugFixState) -> str:
        """Check approval status."""
        status = state.get("approval_status", "pending")
        if status == "approved":
            return "approved"
        elif status == "rejected":
            return "rejected"
        elif status == "modify":
            return "modify"
        return "approved"
    
    async def handle_error(self, state: BugFixState) -> BugFixState:
        """Handle workflow errors."""
        error_msg = state.get("error_message", "Unknown error occurred")
        
        if self.pattern_learner:
            execution_time = int((datetime.now() - state["execution_start"]).total_seconds())
            
            self.pattern_learner.record_bug_fix(
                github_issue_id=state["issue_id"],
                issue_title=state["issue_title"],
                issue_description=state["issue_description"],
                bug_type=state.get("bug_type", "unknown"),
                root_cause=state.get("root_cause", "unknown"),
                fix_strategy=state.get("selected_fix", {}).get("strategy", "failed"),
                pr_number=state.get("pr_info", {}).get("pr_number"),
                success=False,
                execution_time_seconds=execution_time,
                patterns_used=state.get("patterns_used", [])
            )
        
        return state
    
    async def execute(self, github_issue: Dict[str, Any]) -> BugFixState:
        """
        Execute the full bug fix workflow.
        
        Args:
            github_issue: GitHub Issue data
            
        Returns:
            Final workflow state
        """
        initial_state = BugFixState(
            github_issue=github_issue,
            approval_status="pending",
            patterns_used=[]
        )
        
        final_state = await self.workflow.ainvoke(initial_state)
        
        if self.pattern_learner and final_state.get("approval_status") == "approved":
            execution_time = int(
                (datetime.now() - final_state["execution_start"]).total_seconds()
            )
            
            self.pattern_learner.learn_bug_pattern(
                bug_description=final_state["issue_description"],
                root_cause=final_state.get("root_cause", "unknown"),
                affected_code=str(final_state.get("affected_files", [])),
                bug_type=final_state.get("bug_type", "unknown")
            )
            
            self.pattern_learner.learn_fix_pattern(
                bug_description=final_state["issue_description"],
                fix_strategy=final_state.get("selected_fix", {}).get("strategy", ""),
                fix_code=final_state.get("selected_fix", {}).get("code", ""),
                success=True,
                execution_time_seconds=execution_time
            )
            
            self.pattern_learner.record_bug_fix(
                github_issue_id=final_state["issue_id"],
                issue_title=final_state["issue_title"],
                issue_description=final_state["issue_description"],
                bug_type=final_state.get("bug_type", "unknown"),
                root_cause=final_state.get("root_cause", "unknown"),
                fix_strategy=final_state.get("selected_fix", {}).get("strategy", ""),
                pr_number=final_state.get("pr_info", {}).get("pr_number"),
                success=True,
                execution_time_seconds=execution_time,
                patterns_used=final_state.get("patterns_used", [])
            )
        
        return final_state
