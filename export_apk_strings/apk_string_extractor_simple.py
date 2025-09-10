#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK字符串资源提取工具 - 简化版本
纯Python实现，无需外部工具依赖
支持从Android APK文件中提取多语言字符串资源并导出为表格
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
from typing import Dict, List, Tuple, Optional
import re
from tqdm import tqdm


class APKStringExtractor:
    """APK字符串提取器 - 简化版"""
    
    def __init__(self, apk_path: str, supported_langs: List[str] = None):
        """
        初始化APK字符串提取器
        
        Args:
            apk_path: APK文件路径
            supported_langs: 支持的语言列表
        """
        self.apk_path = Path(apk_path)
        if not self.apk_path.exists():
            raise FileNotFoundError(f"APK文件不存在: {apk_path}")
        
        self.temp_dir = None
        self.strings_data = {}
        self.languages = set()
        self.supported_languages = supported_langs  # 支持的业务语言列表
        
        if self.supported_languages:
            print(f"使用指定的语言列表: {', '.join(self.supported_languages)}")
        
    def __enter__(self):
        """上下文管理器入口"""
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def extract_apk(self) -> str:
        """
        解压APK文件到临时目录
        
        Returns:
            解压后的目录路径
        """
        print(f"正在解压APK文件: {self.apk_path}")
        
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zip_ref:
                # 只解压res目录下的文件
                for member in zip_ref.infolist():
                    if member.filename.startswith('res/') and member.filename.endswith('.xml'):
                        try:
                            zip_ref.extract(member, self.temp_dir)
                        except Exception as e:
                            print(f"警告: 无法解压 {member.filename}: {e}")
                            continue
            
            print(f"APK文件已解压到: {self.temp_dir}")
            return self.temp_dir
            
        except Exception as e:
            raise RuntimeError(f"解压APK文件失败: {e}")
    
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
    
    def _try_parse_binary_xml(self, xml_path: str) -> Optional[ET.Element]:
        """
        尝试解析二进制XML文件
        
        Args:
            xml_path: XML文件路径
            
        Returns:
            解析后的根元素，如果失败返回None
        """
        try:
            # 读取文件内容
            with open(xml_path, 'rb') as f:
                content = f.read()
            
            # 检查是否为二进制格式
            if content.startswith(b'\x03\x00\x08\x00') or content.startswith(b'\x02\x00\x0C\x00'):
                print(f"警告: {xml_path} 是二进制XML格式，跳过处理")
                return None
            
            # 尝试作为文本XML解析
            try:
                tree = ET.parse(xml_path)
                return tree.getroot()
            except ET.ParseError:
                # 如果解析失败，尝试清理内容
                content_str = content.decode('utf-8', errors='ignore')
                
                # 移除可能的二进制字符
                content_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', content_str)
                
                # 尝试重新解析
                try:
                    root = ET.fromstring(content_str)
                    return root
                except ET.ParseError:
                    print(f"警告: 无法解析XML文件 {xml_path}")
                    return None
                    
        except Exception as e:
            print(f"警告: 读取文件失败 {xml_path}: {e}")
            return None
    
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
            # 尝试解析XML
            root = self._try_parse_binary_xml(xml_path)
            if root is None:
                return strings
            
            # 查找所有string元素
            for string_elem in root.findall('string'):
                name = string_elem.get('name')
                if name:
                    # 获取文本内容
                    text = self._extract_element_text(string_elem)
                    
                    # 处理转义字符
                    text = self._unescape_xml(text)
                    
                    strings[name] = text
                    
        except Exception as e:
            print(f"警告: 处理文件失败 {xml_path}: {e}")
            
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
    
    def extract_all_strings(self) -> Dict[str, Dict[str, str]]:
        """
        提取所有字符串资源
        
        Returns:
            嵌套字典: {key: {language: value}}
        """
        extract_path = self.extract_apk()
        string_files = self.find_string_files(extract_path)
        
        if not string_files:
            raise ValueError("未找到任何字符串资源文件")
        
        print("正在解析字符串资源...")
        all_strings = {}
        
        for xml_path, lang_code in tqdm(string_files, desc="解析中"):
            strings = self.parse_strings_xml(xml_path)
            self.languages.add(lang_code)
            
            print(f"  {lang_code}: 找到 {len(strings)} 个字符串")
            
            for key, value in strings.items():
                if key not in all_strings:
                    all_strings[key] = {}
                all_strings[key][lang_code] = value
        
        self.strings_data = all_strings
        print(f"\n共提取到 {len(all_strings)} 个字符串键，支持 {len(self.languages)} 种语言")
        
        return all_strings
    
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
            # 使用配置的语言，并保持在APK中存在的语言
            languages = [lang for lang in self.supported_languages if lang in self.languages]
            print(f"\n使用指定的语言列表: {', '.join(languages)}")
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
            
            data.append(row)
        
        # 创建DataFrame并按Key排序
        df = pd.DataFrame(data)
        df = df.sort_values("Key").reset_index(drop=True)
        
        # 重新排列列的顺序：Key, 缺失语言数, 然后是各种语言
        columns = ["Key", "缺失语言数"] + languages
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
            
            # 设置列宽
            worksheet = writer.sheets['Strings']
            for i, column in enumerate(df.columns):
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
        print(f"支持语言数量: {len(df.columns) - 2}")  # 减去Key列和缺失语言数列
        print(f"支持的语言: {', '.join(df.columns[2:])}")  # 从第3列开始才是语言列
        
        # 缺失语言统计
        fully_translated = (df["缺失语言数"] == 0).sum()
        print(f"\n完全翻译的字符串: {fully_translated}/{len(df)} ({(fully_translated/len(df)*100):.1f}%)")
        print(f"平均缺失语言数: {df['缺失语言数'].mean():.1f}")
        
        # 统计每种语言的翻译完成度
        print(f"\n各语言翻译完成度:")
        for lang in df.columns[2:]:  # 从第3列开始才是语言列
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
        description="APK字符串资源提取工具 - 简化版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python apk_string_extractor_simple.py app.apk
  python apk_string_extractor_simple.py app.apk -o strings.xlsx
  python apk_string_extractor_simple.py app.apk -o strings.csv -f csv

注意事项:
  - 纯Python实现，无需外部工具
  - 仅支持文本格式的XML资源文件
  - 对于二进制XML文件会显示警告并跳过
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
        "--languages",
        default=None,
        help="业务支持的多语言列表，用逗号分隔（如：default,zh-rCN,en,ja）"
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
        with APKStringExtractor(args.apk_path, supported_langs) as extractor:
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
        print("\n注意: 如果看到二进制XML警告，说明APK使用了编译后的资源格式。")
        print("这种情况下建议使用完整版工具或先用其他工具反编译APK。")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
