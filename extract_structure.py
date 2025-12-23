#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from datetime import datetime

def generate_project_structure(output_file):
    """يولد هيكل المشروع ويحفظه في ملف"""
    
    # المجلدات التي سيتم تخطيها
    excluded_dirs = {'node_modules', 'venv', '.git', '__pycache__', '.env', 'dist', 'build'}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"هيكل المشروع - تم إنشاؤه في {datetime.now()}\n")
        f.write("======================================\n\n")
        
        # كتابة هيكل المشروع
        for root, dirs, files in os.walk("."):
            # تصفية المجلدات المستثناة
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            level = root.replace(".", "").count(os.sep)
            indent = " " * 4 * level
            subindent = " " * 4 * (level + 1)
            
            # كتابة اسم المجلد
            if level > 0:
                folder_name = os.path.basename(root)
                f.write(f"{indent}📁 {folder_name}/\n")
            else:
                f.write(f"{indent}📁 ./\n")
            
            # كتابة الملفات في المجلد الحالي
            for file in files:
                f.write(f"{subindent}📄 {file}\n")
        
        # إضافة معلومات إضافية
        f.write("\n======================================\n")
        f.write("معلومات إضافية:\n")
        f.write(f"تاريخ الإنشاء: {datetime.now()}\n")
        f.write(f"المسار: {os.getcwd()}\n")
        
        # حساب عدد المجلدات والملفات
        dir_count = 0
        file_count = 0
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            dir_count += len(dirs)
            file_count += len(files)
        
        f.write(f"عدد المجلدات: {dir_count}\n")
        f.write(f"عدد الملفات: {file_count}\n")

if __name__ == "__main__":
    # إنشاء اسم الملف مع التاريخ والوقت
    output_file = f"project_structure_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    
    try:
        generate_project_structure(output_file)
        print(f"تم إنشاء ملف هيكل المشروع: {output_file}")
    except Exception as e:
        print(f"حدث خطأ: {e}")