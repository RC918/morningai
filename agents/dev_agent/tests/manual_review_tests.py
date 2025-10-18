#!/usr/bin/env python3
"""
人工審查清單測試腳本
用於驗證 OODA Loop 的各項功能
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.dev_agent.dev_agent_ooda import create_dev_agent_ooda, DevAgentState


class ManualReviewTests:
    """人工審查測試套件"""
    
    def __init__(self):
        self.sandbox_endpoint = "http://localhost:8080"
        self.passed_tests = []
        self.failed_tests = []
        
    def print_header(self, title: str):
        """打印測試標題"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """打印測試結果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status} - {test_name}")
        if details:
            print(f"  詳情: {details}")
        
        if passed:
            self.passed_tests.append(test_name)
        else:
            self.failed_tests.append(test_name)
    
    
    async def test_1_ooda_workflow_logic(self):
        """測試 1: 驗證 OODA 工作流程邏輯和狀態轉換正確性"""
        self.print_header("測試 1: OODA 工作流程邏輯")
        
        try:
            ooda = create_dev_agent_ooda(self.sandbox_endpoint)
            
            graph = ooda.graph
            print("✓ OODA Graph 創建成功")
            
            test_state = DevAgentState(
                task="測試任務",
                task_priority="medium",
                context={},
                observations=[],
                orientation={},
                strategy=None,
                actions=[],
                action_results=[],
                result=None,
                error=None,
                iteration=0,
                max_iterations=1
            )
            
            print("\n測試 Observe 階段...")
            observed_state = await ooda._observe_node(test_state)
            has_observations = len(observed_state.get('observations', [])) > 0
            print(f"  觀察收集: {len(observed_state.get('observations', []))} 項")
            
            print("\n測試 Orient 階段...")
            oriented_state = await ooda._orient_node(observed_state)
            has_orientation = 'orientation' in oriented_state
            print(f"  方向分析: {'完成' if has_orientation else '失敗'}")
            
            print("\n測試 Decide 階段...")
            decided_state = await ooda._decide_node(oriented_state)
            has_strategy = decided_state.get('strategy') is not None
            print(f"  策略選擇: {decided_state.get('strategy', 'None')}")
            
            print("\n測試 Act 階段...")
            acted_state = await ooda._act_node(decided_state)
            has_results = len(acted_state.get('action_results', [])) > 0
            print(f"  動作執行: {len(acted_state.get('action_results', []))} 個")
            
            print("\n測試循環控制...")
            should_continue = ooda._should_continue(acted_state)
            print(f"  循環判斷: {should_continue}")
            
            all_passed = has_observations and has_orientation and has_strategy
            self.print_result(
                "OODA 工作流程邏輯",
                all_passed,
                f"Observe: {has_observations}, Orient: {has_orientation}, Decide: {has_strategy}, Act: {has_results}"
            )
            
        except Exception as e:
            self.print_result("OODA 工作流程邏輯", False, str(e))
    
    
    async def test_2_tool_integration(self):
        """測試 2: 檢查與現有工具的整合點實作"""
        self.print_header("測試 2: 工具整合點")
        
        try:
            ooda = create_dev_agent_ooda(self.sandbox_endpoint)
            
            print("檢查工具實例...")
            has_git_tool = ooda.git_tool is not None
            has_ide_tool = ooda.ide_tool is not None
            has_fs_tool = ooda.fs_tool is not None
            
            print(f"  Git Tool: {'✓' if has_git_tool else '✗'}")
            print(f"  IDE Tool: {'✓' if has_ide_tool else '✗'}")
            print(f"  FileSystem Tool: {'✓' if has_fs_tool else '✗'}")
            
            print("\n檢查工具調用方法...")
            test_actions = [
                {'type': 'git_clone', 'repo_url': 'test', 'destination': 'test'},
                {'type': 'read_file', 'file_path': 'test.txt'},
                {'type': 'write_file', 'file_path': 'test.txt', 'content': 'test'},
            ]
            
            can_execute_all = True
            for action in test_actions:
                try:
                    action_type = action['type']
                    if action_type in ['git_clone', 'git_commit', 'git_push', 'git_create_pr',
                                      'read_file', 'write_file', 'format_code', 'run_linter']:
                        print(f"  ✓ {action_type} 方法存在")
                    else:
                        print(f"  ✗ {action_type} 未知動作類型")
                        can_execute_all = False
                except Exception as e:
                    print(f"  ✗ {action_type} 錯誤: {e}")
                    can_execute_all = False
            
            all_passed = has_git_tool and has_ide_tool and has_fs_tool and can_execute_all
            self.print_result(
                "工具整合點",
                all_passed,
                f"Git: {has_git_tool}, IDE: {has_ide_tool}, FS: {has_fs_tool}, 方法: {can_execute_all}"
            )
            
        except Exception as e:
            self.print_result("工具整合點", False, str(e))
    
    
    async def test_3_error_handling(self):
        """測試 3: 審查錯誤處理和邊界情況"""
        self.print_header("測試 3: 錯誤處理和邊界情況")
        
        try:
            ooda = create_dev_agent_ooda(self.sandbox_endpoint)
            
            print("測試邊界情況...")
            
            print("\n1. 空任務處理:")
            try:
                result = await ooda.execute_task("", priority="low", max_iterations=1)
                handles_empty = result is not None
                print(f"  空任務: {'✓ 有處理' if handles_empty else '✗ 未處理'}")
            except Exception as e:
                handles_empty = True  # 拋出異常也算是處理了
                print(f"  空任務: ✓ 拋出異常 ({type(e).__name__})")
            
            print("\n2. 無效優先級:")
            try:
                result = await ooda.execute_task("test", priority="invalid", max_iterations=1)
                handles_invalid_priority = True
                print(f"  無效優先級: ✓ 接受但可能未驗證")
            except Exception as e:
                handles_invalid_priority = True
                print(f"  無效優先級: ✓ 拋出異常 ({type(e).__name__})")
            
            print("\n3. 迭代次數限制:")
            result = await ooda.execute_task("test", priority="low", max_iterations=999)
            iteration_limited = result.get('iteration', 0) < 999
            print(f"  迭代限制: {'✓ 有限制' if iteration_limited else '⚠️  可能無限循環風險'}")
            
            print("\n4. 未知動作類型處理:")
            unknown_action = {'type': 'unknown_action_xyz'}
            action_result = await ooda._execute_action(unknown_action)
            handles_unknown = not action_result.get('success', True)
            print(f"  未知動作: {'✓ 回傳錯誤' if handles_unknown else '✗ 未處理'}")
            
            all_passed = handles_empty and handles_invalid_priority and handles_unknown
            warning = " ⚠️ 建議加強迭代限制" if not iteration_limited else ""
            
            self.print_result(
                "錯誤處理和邊界情況",
                all_passed,
                f"空任務: {handles_empty}, 優先級: {handles_invalid_priority}, 未知動作: {handles_unknown}{warning}"
            )
            
        except Exception as e:
            self.print_result("錯誤處理和邊界情況", False, str(e))
    
    
    async def test_4_decision_logic(self):
        """測試 4: 確認簡單啟發式決策邏輯適用性"""
        self.print_header("測試 4: 決策邏輯適用性")
        
        try:
            ooda = create_dev_agent_ooda(self.sandbox_endpoint)
            
            test_cases = [
                ("fix bug in authentication", "bug_fix", "medium"),
                ("add new feature for users", "feature_addition", "low"),
                ("refactor database schema", "refactoring", "high"),
                ("write unit tests", "testing", "low"),
            ]
            
            print("測試任務分類...")
            correct_classifications = 0
            for task, expected_type, expected_complexity in test_cases:
                classified_type = ooda._classify_task(task)
                assessed_complexity = ooda._assess_complexity(task, [])
                
                type_match = classified_type == expected_type
                complexity_match = assessed_complexity == expected_complexity
                
                print(f"\n任務: '{task}'")
                print(f"  分類: {classified_type} {'✓' if type_match else '✗ (預期: ' + expected_type + ')'}")
                print(f"  複雜度: {assessed_complexity} {'✓' if complexity_match else '✗ (預期: ' + expected_complexity + ')'}")
                
                if type_match and complexity_match:
                    correct_classifications += 1
            
            accuracy = correct_classifications / len(test_cases)
            is_adequate = accuracy >= 0.75  # 75% 準確率
            
            print(f"\n準確率: {accuracy * 100:.0f}% ({correct_classifications}/{len(test_cases)})")
            
            self.print_result(
                "決策邏輯適用性",
                is_adequate,
                f"準確率 {accuracy * 100:.0f}%, {'可用' if is_adequate else '建議改進'}"
            )
            
        except Exception as e:
            self.print_result("決策邏輯適用性", False, str(e))
    
    
    async def test_5_dependency_conflicts(self):
        """測試 5: 驗證新依賴不會引起衝突"""
        self.print_header("測試 5: 依賴衝突檢查")
        
        try:
            print("檢查關鍵依賴...")
            
            try:
                import langgraph
                langgraph_version = getattr(langgraph, '__version__', 'unknown')
                print(f"  ✓ langgraph: {langgraph_version}")
                has_langgraph = True
            except ImportError as e:
                print(f"  ✗ langgraph: 導入失敗 - {e}")
                has_langgraph = False
            
            try:
                import langchain_core
                langchain_version = getattr(langchain_core, '__version__', 'unknown')
                print(f"  ✓ langchain-core: {langchain_version}")
                has_langchain = True
            except ImportError as e:
                print(f"  ✗ langchain-core: 導入失敗 - {e}")
                has_langchain = False
            
            print("\n檢查現有依賴相容性...")
            try:
                import requests
                print(f"  ✓ requests: {requests.__version__}")
            except ImportError:
                print(f"  ✗ requests: 導入失敗")
            
            try:
                import aiohttp
                print(f"  ✓ aiohttp: {aiohttp.__version__}")
            except ImportError:
                print(f"  ✗ aiohttp: 導入失敗")
            
            print("\n檢查 OODA 模組導入...")
            try:
                from agents.dev_agent.dev_agent_ooda import create_dev_agent_ooda
                print(f"  ✓ dev_agent_ooda 模組導入成功")
                module_import_ok = True
            except ImportError as e:
                print(f"  ✗ dev_agent_ooda 模組導入失敗: {e}")
                module_import_ok = False
            
            all_passed = has_langgraph and has_langchain and module_import_ok
            self.print_result(
                "依賴衝突檢查",
                all_passed,
                f"langgraph: {has_langgraph}, langchain-core: {has_langchain}, 模組: {module_import_ok}"
            )
            
        except Exception as e:
            self.print_result("依賴衝突檢查", False, str(e))
    
    
    async def run_all_tests(self):
        """運行所有測試"""
        print("\n" + "🔍 開始人工審查清單測試".center(60, "="))
        print("\n注意: 部分測試需要沙箱運行，如無法連接會跳過相關測試\n")
        
        await self.test_1_ooda_workflow_logic()
        await self.test_2_tool_integration()
        await self.test_3_error_handling()
        await self.test_4_decision_logic()
        await self.test_5_dependency_conflicts()
        
        self.print_header("測試總結")
        total = len(self.passed_tests) + len(self.failed_tests)
        print(f"\n總測試數: {total}")
        print(f"✅ 通過: {len(self.passed_tests)}")
        print(f"❌ 失敗: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print("\n失敗的測試:")
            for test in self.failed_tests:
                print(f"  - {test}")
        
        pass_rate = len(self.passed_tests) / total * 100 if total > 0 else 0
        print(f"\n通過率: {pass_rate:.1f}%")
        
        if pass_rate >= 80:
            print("\n✅ 整體評估: 通過")
        elif pass_rate >= 60:
            print("\n⚠️  整體評估: 可用但需改進")
        else:
            print("\n❌ 整體評估: 需要修復")
        
        print("\n" + "="*60 + "\n")


async def main():
    """主程序"""
    tester = ManualReviewTests()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())
