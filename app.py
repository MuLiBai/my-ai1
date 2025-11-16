import streamlit as st
import requests
import time
import json
import os
import csv
from datetime import datetime

# === 新增：多格式记忆系统 ===
class MultiFormatMemory:
    def __init__(self, memory_file="ai_memory", default_format="json"):
        self.memory_file = memory_file
        self.default_format = default_format
        self.memories = self.load_memories()
    
    def get_file_path(self, file_format=None):
        """获取文件路径"""
        if file_format is None:
            file_format = self.default_format
        return f"{self.memory_file}.{file_format}"
    
    def load_memories(self):
        """加载记忆文件 - 支持多种格式"""
        # 尝试按优先级加载不同格式的文件
        formats_to_try = [self.default_format, "json", "csv", "txt"]
        
        for file_format in formats_to_try:
            file_path = self.get_file_path(file_format)
            if os.path.exists(file_path):
                try:
                    if file_format == "json":
                        with open(file_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    elif file_format == "csv":
                        memories = {}
                        with open(file_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                memories[row['key']] = {
                                    "value": row['value'],
                                    "timestamp": row.get('timestamp', '')
                                }
                        return memories
                    elif file_format == "txt":
                        memories = {}
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if ':' in line:
                                    key, value = line.strip().split(':', 1)
                                    memories[key.strip()] = {
                                        "value": value.strip(),
                                        "timestamp": datetime.now().isoformat()
                                    }
                        return memories
                except Exception as e:
                    print(f"加载{file_format}格式记忆失败: {e}")
                    continue
        
        # 如果没有找到任何文件，返回空字典
        return {}
    
    def save_memories(self, file_format=None):
        """保存记忆到文件 - 支持多种格式"""
        if file_format is None:
            file_format = self.default_format
        
        file_path = self.get_file_path(file_format)
        
        try:
            if file_format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.memories, f, ensure_ascii=False, indent=2)
            
            elif file_format == "csv":
                with open(file_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['key', 'value', 'timestamp'])
                    for key, data in self.memories.items():
                        writer.writerow([key, data['value'], data.get('timestamp', '')])
            
            elif file_format == "txt":
                with open(file_path, 'w', encoding='utf-8') as f:
                    for key, data in self.memories.items():
                        f.write(f"{key}: {data['value']}\n")
            
            return True
        except Exception as e:
            print(f"保存{file_format}格式记忆失败: {e}")
            return False
    
    def remember(self, key, value):
        """记住一个事实"""
        self.memories[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        # 保存到所有格式（确保数据同步）
        success = True
        for fmt in ["json", "csv", "txt"]:
            if not self.save_memories(fmt):
                success = False
        return success
    
    def recall(self, key):
        """回忆一个事实"""
        return self.memories.get(key, {}).get("value")
    
    def get_relevant_memories(self, query):
        """获取相关记忆"""
        relevant = []
        for key, data in self.memories.items():
            if key.lower() in query.lower() or query.lower() in key.lower():
                relevant.append(f"{key}: {data['value']}")
        return relevant
    
    def export_memories(self, file_format):
        """导出记忆到指定格式"""
        return self.save_memories(file_format)
    
    def import_memories(self, file_path):
        """从文件导入记忆"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    new_memories = json.load(f)
            elif file_path.endswith('.csv'):
                new_memories = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        new_memories[row['key']] = {
