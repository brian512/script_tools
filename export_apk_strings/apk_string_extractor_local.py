#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK字符串资源提取工具 - 本地工具版本
使用本地Android SDK工具，支持完整的APK反编译功能
"""

import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import argparse
from pathlib import Path
import tempfile
import shutil
import subprocess
from typing import Dict, List, Tuple, Optional
import re
from tqdm import tqdm


class LocalToolManager:
    """本地工具管理器"""
    
    def __init__(self, tools_dir: str):
        self.tools_dir = Path(tools_dir)
        self.aapt_path = self.tools_dir / 'aapt' / 'aapt'
        self.aapt2_path = self.tools_dir / 'aapt' / 'aapt2'
    
    def verify_tools(self) -> bool:
        """验证工具是否可用"""
        if not self.aapt_path.exists():
            print(f"错误: aapt工具不存在: {self.aapt_path}")
            return False
        
        if not self.aapt2_path.exists():
            print(f"错误: aapt2工具不存在: {self.aapt2_path}")
            return False
        
        try:
            # 测试aapt
            result = subprocess.run([str(self.aapt_path), 'version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"错误: aapt工具无法运行")
                return False
            
            # 测试aapt2
            result = subprocess.run([str(self.aapt2_path), 'version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                print(f"错误: aapt2工具无法运行")
                return False
            
            print("工具验证成功 ✓")
            return True
            
        except Exception as e:
            print(f"工具验证失败: {e}")
            return False
    
    def dump_resources(self, apk_path: str) -> Dict[str, str]:
        """
        使用aapt2提取APK资源信息
        
        Args:
            apk_path: APK文件路径
            
        Returns:
            资源信息字典
        """
        print("正在分析APK资源...")
        
        try:
            result = subprocess.run([
                str(self.aapt2_path), 'dump', 'resources', apk_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._parse_aapt2_output(result.stdout)
            else:
                print(f"aapt2分析失败: {result.stderr}")
                return {}
                
        except subprocess.TimeoutExpired:
            print("aapt2分析超时")
            return {}
        except Exception as e:
            print(f"aapt2分析出错: {e}")
            return {}
    
    def _parse_aapt2_output(self, output: str) -> Dict[str, str]:
        """解析aapt2输出"""
        resources = {}
        lines = output.split('\n')
        
        current_package = None
        current_type = None
        
        for line in lines:
            line = line.strip()
            
            # 解析包名
            if line.startswith('Package'):
                match = re.search(r'Package.*?name=(\w+)', line)
                if match:
                    current_package = match.group(1)
            
            # 解析资源类型
            elif line.startswith('type') and 'string' in line:
                current_type = 'string'
            
            # 解析字符串资源
            elif current_type == 'string' and 'resource' in line:
                match = re.search(r'resource\s+\w+:string/(\w+)', line)
                if match:
                    string_name = match.group(1)
                    resources[string_name] = ''
        
        return resources


class APKStringExtractor:
    """APK字符串提取器 - 本地工具版本"""
    
    def __init__(self, apk_path: str, tools_dir: str = None, lang_config: str = None, supported_langs: List[str] = None):
        """
        初始化APK字符串提取器
        
        Args:
            apk_path: APK文件路径
            tools_dir: 工具目录路径
            lang_config: 语言配置文件路径
            supported_langs: 支持的语言列表，优先级高于配置文件
        """
        self.apk_path = Path(apk_path)
        if not self.apk_path.exists():
            raise FileNotFoundError(f"APK文件不存在: {apk_path}")
        
        # 设置工具目录
        if tools_dir is None:
            tools_dir = Path(__file__).parent / 'tools'
        
        self.tool_manager = LocalToolManager(tools_dir)
        self.temp_dir = None
        self.strings_data = {}
        self.languages = set()
        self.supported_languages = None  # 支持的业务语言列表
        
        # 优先使用传入的语言列表
        if supported_langs:
            self.supported_languages = supported_langs
            print(f"使用命令行指定的语言列表: {', '.join(self.supported_languages)}")
        # 其次使用语言配置文件
        elif lang_config:
            self.supported_languages = self.load_language_config(lang_config)
            print(f"加载语言配置: {lang_config}")
            print(f"支持的业务语言: {', '.join(self.supported_languages)}")
        
    def __enter__(self):
        """上下文管理器入口"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 验证工具
        if not self.tool_manager.verify_tools():
            raise RuntimeError("工具验证失败，请确保已正确拷贝aapt和aapt2工具")
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def load_language_config(self, config_path: str) -> List[str]:
        """
        加载语言配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            支持的语言列表
        """
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"警告: 语言配置文件不存在: {config_path}")
            return None
            
        languages = []
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if line and not line.startswith('#'):
                        languages.append(line)
            
            if not languages:
                print(f"警告: 语言配置文件为空: {config_path}")
                return None
                
            return languages
            
        except Exception as e:
            print(f"错误: 无法读取语言配置文件: {e}")
            return None
    
    def extract_apk_with_aapt(self) -> str:
        """
        使用aapt工具反编译APK
        
        Returns:
            反编译后的目录路径
        """
        print(f"正在使用aapt反编译APK: {self.apk_path}")
        
        try:
            # 使用aapt dump xmltree来提取资源
            output_dir = Path(self.temp_dir) / "extracted"
            output_dir.mkdir(exist_ok=True)
            
            # 先尝试直接解压APK
            with zipfile.ZipFile(self.apk_path, 'r') as zip_ref:
                # 解压所有res目录下的文件
                for member in zip_ref.infolist():
                    if member.filename.startswith('res/'):
                        try:
                            zip_ref.extract(member, output_dir)
                        except Exception:
                            # 忽略解压失败的文件
                            continue
            
            print(f"APK已反编译到: {output_dir}")
            return str(output_dir)
            
        except Exception as e:
            raise RuntimeError(f"APK反编译失败: {e}")
    
    def extract_strings_with_aapt(self) -> Dict[str, Dict[str, str]]:
        """
        使用aapt工具提取字符串资源
        
        Returns:
            嵌套字典: {key: {language: value}}
        """
        print("正在使用aapt提取字符串资源...")
        
        all_strings = {}
        
        try:
            # 使用aapt dump strings命令
            result = subprocess.run([
                str(self.tool_manager.aapt_path), 'dump', 'strings', str(self.apk_path)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self._parse_aapt_strings_output(result.stdout, all_strings)
            else:
                print(f"aapt dump strings失败，使用备用方法")
                # 使用备用方法：直接解析XML文件
                self._extract_strings_from_xml(all_strings)
                
        except Exception as e:
            print(f"aapt提取失败，使用备用方法: {e}")
            self._extract_strings_from_xml(all_strings)
        
        return all_strings
    
    def _extract_strings_from_xml(self, all_strings: Dict[str, Dict[str, str]]):
        """从XML文件直接提取字符串（备用方法）"""
        extract_path = self.extract_apk_with_aapt()
        string_files = self.find_string_files(extract_path)
        
        if not string_files:
            return
        
        print("正在解析XML字符串文件...")
        
        for xml_path, lang_code in tqdm(string_files, desc="解析中"):
            strings = self.parse_strings_xml(xml_path)
            self.languages.add(lang_code)
            
            for key, value in strings.items():
                if key not in all_strings:
                    all_strings[key] = {}
                all_strings[key][lang_code] = value
    
    def _parse_aapt_strings_output(self, output: str, all_strings: Dict[str, Dict[str, str]]):
        """解析aapt dump strings的输出"""
        lines = output.split('\n')
        current_locale = 'default'
        
        for line in lines:
            line = line.strip()
            
            # 解析语言环境
            if 'String pool of' in line:
                if 'resources.arsc' in line:
                    # 尝试从文件名中提取语言信息
                    continue
            
            # 解析字符串条目
            if line.startswith('String #'):
                match = re.search(r'String #\d+: (.+)', line)
                if match:
                    string_value = match.group(1).strip('"')
                    # 这里需要更复杂的逻辑来匹配字符串名称
                    # 暂时使用备用方法
                    pass
        
        # 如果aapt解析不够详细，回退到XML解析
        if not all_strings:
            self._extract_strings_from_xml(all_strings)
    
    def find_string_files(self, extract_path: str) -> List[Tuple[str, str]]:
        """
        查找所有字符串资源文件
        
        Args:
            extract_path: APK解压路径
            
        Returns:
            (文件路径, 语言代码) 的列表
        """
        string_files = []
        res_path = Path(extract_path) / "res"
        
        if not res_path.exists():
            print("警告: 未找到res目录")
            return string_files
        
        # 查找所有values目录
        for values_dir in res_path.glob("values*"):
            if values_dir.is_dir():
                strings_xml = values_dir / "strings.xml"
                if strings_xml.exists():
                    # 提取语言代码
                    lang_code = self._extract_language_code(values_dir.name)
                    string_files.append((str(strings_xml), lang_code))
        
        print(f"找到 {len(string_files)} 个字符串资源文件")
        return string_files
    
    def _extract_language_code(self, values_dir_name: str) -> str:
        """
        从values目录名提取语言代码
        
        Args:
            values_dir_name: values目录名，如 "values", "values-zh", "values-en-rUS"
            
        Returns:
            语言代码，默认语言返回"default"
        """
        if values_dir_name == "values":
            return "default"
        
        # 移除"values-"前缀
        lang_part = values_dir_name.replace("values-", "")
        
        # 处理特殊格式，如"en-rUS" -> "en-US"
        lang_part = re.sub(r'-r([A-Z]{2})', r'-\1', lang_part)
        
        return lang_part
    
    def parse_strings_xml(self, xml_path: str) -> Dict[str, str]:
        """
        解析strings.xml文件
        
        Args:
            xml_path: strings.xml文件路径
            
        Returns:
            字符串键值对字典
        """
        strings = {}
        
        try:
            # 首先尝试使用aapt dump xmltree来解析二进制XML
            result = subprocess.run([
                str(self.tool_manager.aapt_path), 'dump', 'xmltree', 
                str(self.apk_path), xml_path.replace(str(Path(self.temp_dir) / "extracted"), "").lstrip('/')
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                strings = self._parse_aapt_xmltree_output(result.stdout)
                if strings:
                    return strings
            
            # 如果aapt解析失败，尝试直接解析XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 查找所有string元素
            for string_elem in root.findall('string'):
                name = string_elem.get('name')
                if name:
                    # 获取文本内容，处理可能的HTML标签
                    text = self._extract_element_text(string_elem)
                    
                    # 处理转义字符
                    text = self._unescape_xml(text)
                    
                    strings[name] = text
                    
        except ET.ParseError as e:
            print(f"警告: 解析XML文件失败 {xml_path}: {e}")
        except Exception as e:
            print(f"警告: 处理文件失败 {xml_path}: {e}")
            
        return strings
    
    def _parse_aapt_xmltree_output(self, output: str) -> Dict[str, str]:
        """解析aapt dump xmltree的输出"""
        strings = {}
        lines = output.split('\n')
        
        current_string_name = None
        for line in lines:
            # 查找string元素
            if 'E: string' in line and 'name=' in line:
                match = re.search(r'name="([^"]+)"', line)
                if match:
                    current_string_name = match.group(1)
            
            # 查找文本内容
            elif current_string_name and 'T:' in line:
                match = re.search(r'T: "([^"]*)"', line)
                if match:
                    text = match.group(1)
                    strings[current_string_name] = self._unescape_xml(text)
                    current_string_name = None
        
        return strings
    
    def _extract_element_text(self, element: ET.Element) -> str:
        """
        提取元素的完整文本内容，包括子元素
        
        Args:
            element: XML元素
            
        Returns:
            完整的文本内容
        """
        text_parts = []
        
        # 添加元素自身的文本
        if element.text:
            text_parts.append(element.text)
        
        # 递归处理子元素
        for child in element:
            # 添加子元素的文本
            child_text = self._extract_element_text(child)
            if child_text:
                text_parts.append(child_text)
            
            # 添加子元素后的尾部文本
            if child.tail:
                text_parts.append(child.tail)
        
        return ''.join(text_parts)
    
    def _unescape_xml(self, text: str) -> str:
        """
        反转义XML文本
        
        Args:
            text: XML文本
            
        Returns:
            反转义后的文本
        """
        if not text:
            return ""
            
        # XML基本转义
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        
        # Android特殊转义
        text = text.replace('\\"', '"')
        text = text.replace("\\'", "'")
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        text = text.replace('\\\\', '\\')
        
        return text.strip()
    
    def _extract_placeholders(self, text: str) -> List[str]:
        """
        从字符串中提取所有占位符
        
        Args:
            text: 输入字符串
            
        Returns:
            占位符列表，保持原始顺序
        """
        if not text:
            return []
        
        placeholders = []
        
        # 先处理编号占位符 %1$s, %2$s 等
        numbered_matches = re.finditer(r'%(\d+)\$[sd]', text)
        for match in numbered_matches:
            placeholders.append(match.group(0))
        
        # 再处理简单占位符 %s, %d 等
        simple_matches = re.finditer(r'%[sd](?![0-9])', text)
        for match in simple_matches:
            placeholders.append(match.group(0))
        
        return placeholders
    
    def _compare_placeholders(self, default_text: str, other_text: str) -> bool:
        """
        比较两个字符串的占位符是否一致（忽略顺序，只比较数量和类型）。
        兼容 %1$s 与 %s 视为同一类型。
        
        Args:
            default_text: 默认语言的文本
            other_text: 其他语言的文本
            
        Returns:
            True表示占位符一致，False表示不一致
        """
        if not default_text or not other_text:
            return default_text == other_text
        
        default_placeholders = self._extract_placeholders(default_text)
        other_placeholders = self._extract_placeholders(other_text)
        
        # 将占位符标准化为类型列表（例如 '%1$s' 和 '%s' → 's'）
        def normalize_to_types(placeholders: List[str]) -> List[str]:
            types = []
            for ph in placeholders:
                t = 's' if ph.endswith('s') else ('d' if ph.endswith('d') else '')
                if t:
                    types.append(t)
            return types
        
        from collections import Counter
        return Counter(normalize_to_types(default_placeholders)) == Counter(normalize_to_types(other_placeholders))
    
    def _count_placeholder_anomalies(self, translations: Dict[str, str], languages: List[str]) -> int:
        """
        计算占位符异常数量（兼容旧逻辑，保留）
        """
        return len(self._get_placeholder_anomaly_languages(translations, languages))

    def _get_placeholder_anomaly_languages(self, translations: Dict[str, str], languages: List[str]) -> List[str]:
        """
        获取占位符异常的语言列表
        
        Args:
            translations: 翻译字典 {language: text}
            languages: 语言列表（默认语言应为第一个）
        Returns:
            占位符异常语言代码列表，例如 ["ar", "de"]
        """
        if not translations or len(languages) <= 1:
            return []
        
        # 获取默认语言文本
        default_lang = languages[0] if languages else "default"
        default_text = translations.get(default_lang, "")
        
        if not default_text:
            return []
        
        anomaly_langs: List[str] = []
        
        # 检查其他语言与默认语言的占位符是否一致
        for lang in languages[1:]:  # 跳过默认语言
            other_text = translations.get(lang, "")
            if other_text and not self._compare_placeholders(default_text, other_text):
                anomaly_langs.append(lang)
        
        return anomaly_langs
    
    def extract_all_strings(self) -> Dict[str, Dict[str, str]]:
        """
        提取所有字符串资源
        
        Returns:
            嵌套字典: {key: {language: value}}
        """
        # 使用aapt2提取字符串资源（优先方法）
        all_strings = self.extract_strings_with_aapt2()
        
        # 如果aapt2提取失败，使用XML解析作为备用方法
        if not all_strings:
            print("aapt2提取失败，使用XML解析备用方法...")
            self._extract_strings_from_xml(all_strings)
        
        self.strings_data = all_strings
        print(f"共提取到 {len(all_strings)} 个字符串键，支持 {len(self.languages)} 种语言")
        
        return all_strings
    
    def extract_strings_with_aapt2(self) -> Dict[str, Dict[str, str]]:
        """
        使用aapt2提取字符串资源
        
        Returns:
            嵌套字典: {key: {language: value}}
        """
        print("正在使用aapt2提取字符串资源...")
        
        all_strings = {}
        
        try:
            result = subprocess.run([
                str(self.tool_manager.aapt2_path), 'dump', 'resources', str(self.apk_path)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                all_strings = self._parse_aapt2_resources_output(result.stdout)
            else:
                print(f"aapt2执行失败: {result.stderr}")
                
        except Exception as e:
            print(f"aapt2执行出错: {e}")
        
        return all_strings
    
    def _parse_aapt2_resources_output(self, output: str) -> Dict[str, Dict[str, str]]:
        """
        解析aapt2 dump resources的输出
        
        Args:
            output: aapt2输出文本
            
        Returns:
            解析后的字符串字典
        """
        strings_data = {}
        lines = output.split('\n')
        
        current_string_name = None
        current_string_data = {}
        in_string_section = False
        
        for line in lines:
            line = line.strip()
            
            # 检测字符串类型开始
            if 'type string' in line:
                in_string_section = True
                continue
            
            # 检测其他类型开始，退出字符串处理
            if in_string_section and line.startswith('type ') and 'string' not in line:
                in_string_section = False
                continue
            
            if not in_string_section:
                continue
            
            # 解析字符串资源定义
            if line.startswith('resource ') and 'string/' in line:
                # 保存上一个字符串
                if current_string_name and current_string_data:
                    strings_data[current_string_name] = current_string_data
                
                # 提取字符串名称
                match = re.search(r'string/([^\s]+)', line)
                if match:
                    current_string_name = match.group(1)
                    current_string_data = {}
            
            # 解析字符串值
            elif current_string_name and '"' in line:
                # 匹配格式: () "value" 或 (language) "value"
                match = re.match(r'\s*\(([^)]*)\)\s*"([^"]*)"', line)
                if match:
                    language = match.group(1)
                    value = match.group(2)
                    
                    if not language:  # 默认语言
                        language = "default"
                    
                    current_string_data[language] = value
                    self.languages.add(language)
        
        # 处理最后一个字符串
        if current_string_name and current_string_data:
            strings_data[current_string_name] = current_string_data
        
        return strings_data
    
    def create_dataframe(self) -> pd.DataFrame:
        """
        创建包含所有字符串数据的DataFrame
        
        Returns:
            pandas DataFrame
        """
        if not self.strings_data:
            raise ValueError("请先调用extract_all_strings()方法")
        
        # 准备数据
        data = []
        
        # 确定要导出的语言列表
        if self.supported_languages:
            # 使用配置文件中的语言，并保持在APK中存在的语言
            languages = [lang for lang in self.supported_languages if lang in self.languages]
            print(f"\n使用配置的语言列表: {', '.join(languages)}")
            print(f"过滤掉的语言: {', '.join(set(self.languages) - set(languages))}")
        else:
            # 使用所有检测到的语言
            languages = sorted(self.languages)
            if "default" in languages:
                languages.remove("default")
                languages.insert(0, "default")
        
        for key, translations in self.strings_data.items():
            row = {"Key": key}
            
            # 统计缺失的多语言数量
            missing_count = 0
            for lang in languages:
                translation = translations.get(lang, "")
                row[lang] = translation
                if not translation:  # 如果翻译为空，则计为缺失
                    missing_count += 1
            
            # 在Key列后插入缺失语言统计列
            row["缺失语言数"] = missing_count
            
            # 计算占位符异常：改为列出具体异常语言，用、分隔；无异常为空
            anomaly_langs = self._get_placeholder_anomaly_languages(translations, languages)
            row["占位符异常"] = "、".join(anomaly_langs)
            
            data.append(row)
        
        # 创建DataFrame并按Key排序
        df = pd.DataFrame(data)
        df = df.sort_values("Key").reset_index(drop=True)
        
        # 重新排列列的顺序：Key, 缺失语言数, 占位符异常, 然后是各种语言
        columns = ["Key", "缺失语言数", "占位符异常"] + languages
        df = df[columns]
        
        return df
    
    def export_to_csv(self, output_path: str):
        """
        导出到CSV文件
        
        Args:
            output_path: 输出文件路径
        """
        df = self.create_dataframe()
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"字符串资源已导出到CSV文件: {output_path}")
        self._print_summary(df)
    
    def export_to_excel(self, output_path: str):
        """
        导出到Excel文件
        
        Args:
            output_path: 输出文件路径
        """
        df = self.create_dataframe()
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Strings', index=False)
            
            # 设置列宽 - 修复列名过多的问题
            worksheet = writer.sheets['Strings']
            for i, column in enumerate(df.columns):
                if i >= 26:  # 超过Z列，使用默认宽度
                    break
                max_length = max(
                    df[column].astype(str).map(len).max(),
                    len(column)
                )
                # 限制最大宽度
                max_length = min(max_length, 50)
                worksheet.column_dimensions[chr(65 + i)].width = max_length + 2
        
        print(f"字符串资源已导出到Excel文件: {output_path}")
        self._print_summary(df)
    
    def _print_summary(self, df: pd.DataFrame):
        """打印提取结果摘要"""
        print(f"\n=== 提取结果摘要 ===")
        print(f"总字符串数量: {len(df)}")
        print(f"支持语言数量: {len(df.columns) - 3}")  # 减去Key列、缺失语言数列和占位符异常列
        print(f"支持的语言: {', '.join(df.columns[3:])}")  # 从第4列开始才是语言列
        
        # 缺失语言统计
        fully_translated = (df["缺失语言数"] == 0).sum()
        print(f"\n完全翻译的字符串: {fully_translated}/{len(df)} ({(fully_translated/len(df)*100):.1f}%)")
        print(f"平均缺失语言数: {df['缺失语言数'].mean():.1f}")
        
        # 占位符异常统计（基于列表列）
        no_placeholder_anomalies = (df["占位符异常"] == "").sum()
        print(f"\n占位符正常的字符串: {no_placeholder_anomalies}/{len(df)} ({(no_placeholder_anomalies/len(df)*100):.1f}%)")
        # 统计平均异常语言数
        avg_anomaly_langs = df["占位符异常"].apply(lambda x: 0 if x == "" else len(str(x).split("、"))).mean()
        print(f"平均占位符异常语言数: {avg_anomaly_langs:.1f}")
        
        # 统计每种语言的翻译完成度
        print(f"\n各语言翻译完成度:")
        for lang in df.columns[3:]:  # 从第4列开始才是语言列
            non_empty = (df[lang] != "").sum()
            percentage = (non_empty / len(df)) * 100
            print(f"  {lang}: {non_empty}/{len(df)} ({percentage:.1f}%)")


def check_requirements():
    """检查运行环境"""
    print("正在检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("错误: 需要Python 3.6或更高版本")
        sys.exit(1)
    
    # 检查必要的模块
    required_modules = ['pandas', 'openpyxl', 'tqdm']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"错误: 缺少必要的Python模块: {', '.join(missing_modules)}")
        print("请运行: pip install pandas openpyxl tqdm")
        sys.exit(1)
    
    print("运行环境检查完成 ✓")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="APK字符串资源提取工具 - 本地工具版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python apk_string_extractor_local.py app.apk
  python apk_string_extractor_local.py app.apk -o strings.xlsx
  python apk_string_extractor_local.py app.apk -o strings.csv -f csv

特点:
  - 使用本地Android SDK工具
  - 支持二进制XML格式
  - 更好的兼容性和可靠性
        """
    )
    
    parser.add_argument(
        "apk_path",
        help="APK文件路径"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="strings.xlsx",
        help="输出文件路径 (默认: strings.xlsx)"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["excel", "csv"],
        default="excel",
        help="输出格式 (默认: excel)"
    )
    
    parser.add_argument(
        "--tools-dir",
        default=None,
        help="工具目录路径（默认: ./tools）"
    )
    
    parser.add_argument(
        "-l", "--lang-config",
        default=None,
        help="语言配置文件路径，每行一个语言代码，用于过滤业务需要的多语言"
    )
    
    parser.add_argument(
        "--languages",
        default=None,
        help="业务支持的多语言列表，用逗号分隔（如：default,zh-rCN,en,ja）。此参数优先级高于 -l 参数"
    )
    
    args = parser.parse_args()
    
    try:
        # 检查环境
        check_requirements()
        
        # 检查APK文件
        if not os.path.exists(args.apk_path):
            print(f"错误: APK文件不存在: {args.apk_path}")
            sys.exit(1)
        
        # 解析语言列表参数
        supported_langs = None
        if args.languages:
            supported_langs = [lang.strip() for lang in args.languages.split(',') if lang.strip()]
            print(f"解析的语言列表: {supported_langs}")
        
        # 提取字符串
        tools_dir = args.tools_dir or (Path(__file__).parent / 'tools')
        with APKStringExtractor(args.apk_path, tools_dir, args.lang_config, supported_langs) as extractor:
            extractor.extract_all_strings()
            
            # 导出文件
            if args.format == "csv":
                if not args.output.endswith('.csv'):
                    args.output = args.output.rsplit('.', 1)[0] + '.csv'
                extractor.export_to_csv(args.output)
            else:
                if not args.output.endswith('.xlsx'):
                    args.output = args.output.rsplit('.', 1)[0] + '.xlsx'
                extractor.export_to_excel(args.output)
        
        print("\n🎉 提取完成!")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
