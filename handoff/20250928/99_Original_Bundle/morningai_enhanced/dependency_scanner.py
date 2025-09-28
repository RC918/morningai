"""
依賴項安全掃描器
檢查專案依賴項的安全漏洞
"""

import json
import subprocess
import requests
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

class DependencyScanner:
    """依賴項安全掃描器"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.logger = self._setup_logger()
        self.vulnerability_db = {}
        
    def _setup_logger(self) -> logging.Logger:
        """設置日誌記錄器"""
        logger = logging.getLogger('dependency_scanner')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def scan_python_dependencies(self) -> Dict[str, Any]:
        """掃描Python依賴項"""
        results = {
            'scan_time': datetime.now().isoformat(),
            'vulnerabilities': [],
            'total_packages': 0,
            'vulnerable_packages': 0
        }
        
        try:
            # 檢查requirements.txt文件
            requirements_files = [
                'requirements.txt',
                'requirements-dev.txt',
                'Pipfile',
                'pyproject.toml'
            ]
            
            dependencies = []
            for req_file in requirements_files:
                file_path = os.path.join(self.project_path, req_file)
                if os.path.exists(file_path):
                    dependencies.extend(self._parse_requirements_file(file_path))
            
            # 如果沒有找到依賴文件，嘗試從pip freeze獲取
            if not dependencies:
                dependencies = self._get_installed_packages()
            
            results['total_packages'] = len(dependencies)
            
            # 檢查每個依賴項的安全漏洞
            for package in dependencies:
                vulnerabilities = self._check_package_vulnerabilities(package)
                if vulnerabilities:
                    results['vulnerabilities'].extend(vulnerabilities)
                    results['vulnerable_packages'] += 1
            
            self.logger.info(f"掃描完成: {results['total_packages']} 個包，發現 {len(results['vulnerabilities'])} 個漏洞")
            
        except Exception as e:
            self.logger.error(f"Python依賴項掃描失敗: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def scan_nodejs_dependencies(self) -> Dict[str, Any]:
        """掃描Node.js依賴項"""
        results = {
            'scan_time': datetime.now().isoformat(),
            'vulnerabilities': [],
            'total_packages': 0,
            'vulnerable_packages': 0
        }
        
        try:
            package_json_path = os.path.join(self.project_path, 'package.json')
            if not os.path.exists(package_json_path):
                return results
            
            # 使用npm audit檢查漏洞
            try:
                result = subprocess.run(
                    ['npm', 'audit', '--json'],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 or result.stdout:
                    audit_data = json.loads(result.stdout)
                    results.update(self._parse_npm_audit_results(audit_data))
                
            except subprocess.TimeoutExpired:
                self.logger.warning("npm audit 超時")
            except json.JSONDecodeError:
                self.logger.warning("無法解析npm audit輸出")
            except FileNotFoundError:
                self.logger.warning("npm命令未找到，跳過Node.js依賴掃描")
            
        except Exception as e:
            self.logger.error(f"Node.js依賴項掃描失敗: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _parse_requirements_file(self, file_path: str) -> List[Dict[str, str]]:
        """解析requirements文件"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 簡單解析包名和版本
                        if '==' in line:
                            name, version = line.split('==', 1)
                            dependencies.append({
                                'name': name.strip(),
                                'version': version.strip(),
                                'source': file_path
                            })
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies.append({
                                'name': name.strip(),
                                'version': version.strip(),
                                'source': file_path,
                                'constraint': '>='
                            })
                        else:
                            dependencies.append({
                                'name': line.strip(),
                                'version': 'unknown',
                                'source': file_path
                            })
        except Exception as e:
            self.logger.error(f"解析 {file_path} 失敗: {str(e)}")
        
        return dependencies
    
    def _get_installed_packages(self) -> List[Dict[str, str]]:
        """獲取已安裝的Python包"""
        dependencies = []
        
        try:
            result = subprocess.run(
                ['pip', 'freeze'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and '==' in line:
                        name, version = line.split('==', 1)
                        dependencies.append({
                            'name': name.strip(),
                            'version': version.strip(),
                            'source': 'pip freeze'
                        })
        except Exception as e:
            self.logger.error(f"獲取已安裝包失敗: {str(e)}")
        
        return dependencies
    
    def _check_package_vulnerabilities(self, package: Dict[str, str]) -> List[Dict[str, Any]]:
        """檢查單個包的安全漏洞"""
        vulnerabilities = []
        
        try:
            # 使用PyUp.io的安全數據庫API（示例）
            # 實際應用中應該使用官方的安全數據庫
            package_name = package['name'].lower()
            package_version = package['version']
            
            # 模擬已知的漏洞檢查
            known_vulnerabilities = self._get_known_vulnerabilities()
            
            if package_name in known_vulnerabilities:
                for vuln in known_vulnerabilities[package_name]:
                    if self._version_affected(package_version, vuln['affected_versions']):
                        vulnerabilities.append({
                            'package_name': package_name,
                            'package_version': package_version,
                            'vulnerability_id': vuln['id'],
                            'severity': vuln['severity'],
                            'description': vuln['description'],
                            'fixed_version': vuln.get('fixed_version'),
                            'cve_id': vuln.get('cve_id'),
                            'source': package.get('source', 'unknown')
                        })
            
        except Exception as e:
            self.logger.error(f"檢查 {package['name']} 漏洞失敗: {str(e)}")
        
        return vulnerabilities
    
    def _get_known_vulnerabilities(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取已知漏洞數據庫"""
        # 這是一個簡化的示例，實際應用中應該從官方安全數據庫獲取
        return {
            'flask': [
                {
                    'id': 'VULN-001',
                    'severity': 'medium',
                    'description': 'Flask版本存在XSS漏洞',
                    'affected_versions': ['<2.0.0'],
                    'fixed_version': '2.0.0',
                    'cve_id': 'CVE-2021-XXXX'
                }
            ],
            'requests': [
                {
                    'id': 'VULN-002',
                    'severity': 'high',
                    'description': 'Requests庫存在SSL驗證繞過漏洞',
                    'affected_versions': ['<2.25.0'],
                    'fixed_version': '2.25.0',
                    'cve_id': 'CVE-2021-YYYY'
                }
            ],
            'pillow': [
                {
                    'id': 'VULN-003',
                    'severity': 'critical',
                    'description': 'Pillow存在遠程代碼執行漏洞',
                    'affected_versions': ['<8.3.2'],
                    'fixed_version': '8.3.2',
                    'cve_id': 'CVE-2021-ZZZZ'
                }
            ]
        }
    
    def _version_affected(self, current_version: str, affected_versions: List[str]) -> bool:
        """檢查版本是否受影響"""
        if current_version == 'unknown':
            return True  # 未知版本視為可能受影響
        
        try:
            from packaging import version
            current_ver = version.parse(current_version)
            
            for affected_range in affected_versions:
                if affected_range.startswith('<'):
                    max_version = version.parse(affected_range[1:])
                    if current_ver < max_version:
                        return True
                elif affected_range.startswith('<='):
                    max_version = version.parse(affected_range[2:])
                    if current_ver <= max_version:
                        return True
                elif affected_range.startswith('>='):
                    min_version = version.parse(affected_range[2:])
                    if current_ver >= min_version:
                        return True
                elif affected_range.startswith('>'):
                    min_version = version.parse(affected_range[1:])
                    if current_ver > min_version:
                        return True
                elif affected_range == current_version:
                    return True
                    
        except Exception as e:
            self.logger.warning(f"版本比較失敗: {str(e)}")
            return True  # 比較失敗時保守處理
        
        return False
    
    def _parse_npm_audit_results(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析npm audit結果"""
        results = {
            'total_packages': 0,
            'vulnerable_packages': 0,
            'vulnerabilities': []
        }
        
        try:
            if 'vulnerabilities' in audit_data:
                for vuln_id, vuln_data in audit_data['vulnerabilities'].items():
                    results['vulnerabilities'].append({
                        'package_name': vuln_data.get('name', 'unknown'),
                        'package_version': vuln_data.get('version', 'unknown'),
                        'vulnerability_id': vuln_id,
                        'severity': vuln_data.get('severity', 'unknown'),
                        'description': vuln_data.get('title', ''),
                        'cve_id': vuln_data.get('cve', []),
                        'source': 'npm audit'
                    })
                
                results['vulnerable_packages'] = len(audit_data['vulnerabilities'])
            
            if 'metadata' in audit_data:
                results['total_packages'] = audit_data['metadata'].get('totalDependencies', 0)
                
        except Exception as e:
            self.logger.error(f"解析npm audit結果失敗: {str(e)}")
        
        return results
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全報告"""
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'project_path': self.project_path,
            'python_scan': self.scan_python_dependencies(),
            'nodejs_scan': self.scan_nodejs_dependencies(),
            'summary': {},
            'recommendations': []
        }
        
        # 生成摘要
        total_vulns = (
            len(report['python_scan'].get('vulnerabilities', [])) +
            len(report['nodejs_scan'].get('vulnerabilities', []))
        )
        
        critical_vulns = sum(
            1 for vuln in (
                report['python_scan'].get('vulnerabilities', []) +
                report['nodejs_scan'].get('vulnerabilities', [])
            )
            if vuln.get('severity') == 'critical'
        )
        
        high_vulns = sum(
            1 for vuln in (
                report['python_scan'].get('vulnerabilities', []) +
                report['nodejs_scan'].get('vulnerabilities', [])
            )
            if vuln.get('severity') == 'high'
        )
        
        report['summary'] = {
            'total_vulnerabilities': total_vulns,
            'critical_vulnerabilities': critical_vulns,
            'high_vulnerabilities': high_vulns,
            'risk_level': self._calculate_risk_level(critical_vulns, high_vulns, total_vulns)
        }
        
        # 生成建議
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _calculate_risk_level(self, critical: int, high: int, total: int) -> str:
        """計算風險等級"""
        if critical > 0:
            return 'critical'
        elif high > 3:
            return 'high'
        elif high > 0 or total > 10:
            return 'medium'
        elif total > 0:
            return 'low'
        else:
            return 'none'
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成安全建議"""
        recommendations = []
        
        # 基於掃描結果生成建議
        if report['summary']['critical_vulnerabilities'] > 0:
            recommendations.append("立即更新存在嚴重漏洞的依賴項")
        
        if report['summary']['high_vulnerabilities'] > 0:
            recommendations.append("盡快更新存在高危漏洞的依賴項")
        
        if report['summary']['total_vulnerabilities'] > 10:
            recommendations.append("建立定期的依賴項安全掃描流程")
        
        # 通用建議
        recommendations.extend([
            "啟用自動依賴項更新",
            "在CI/CD流水線中集成安全掃描",
            "定期審查和更新依賴項",
            "使用依賴項鎖定文件（如requirements.txt、package-lock.json）",
            "監控安全公告和CVE數據庫"
        ])
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """保存安全報告"""
        if output_file is None:
            output_file = f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"安全報告已保存到: {output_file}")
            
        except Exception as e:
            self.logger.error(f"保存報告失敗: {str(e)}")

def main():
    """主函數，用於命令行執行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='依賴項安全掃描器')
    parser.add_argument('project_path', help='專案路徑')
    parser.add_argument('--output', '-o', help='輸出文件路徑')
    
    args = parser.parse_args()
    
    scanner = DependencyScanner(args.project_path)
    report = scanner.generate_security_report()
    
    # 打印摘要
    print(f"\n=== 安全掃描報告 ===")
    print(f"掃描時間: {report['scan_timestamp']}")
    print(f"專案路徑: {report['project_path']}")
    print(f"總漏洞數: {report['summary']['total_vulnerabilities']}")
    print(f"嚴重漏洞: {report['summary']['critical_vulnerabilities']}")
    print(f"高危漏洞: {report['summary']['high_vulnerabilities']}")
    print(f"風險等級: {report['summary']['risk_level']}")
    
    # 保存報告
    scanner.save_report(report, args.output)

if __name__ == '__main__':
    main()

