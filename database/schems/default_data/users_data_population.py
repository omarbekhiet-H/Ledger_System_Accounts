import os
import subprocess
from datetime import datetime

# إنشاء اسم الملف
output_file = f"project_structure_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

# محاولة استخدام tree إذا كان متاحاً
try:
    result = subprocess.run([
        'tree', '-I', 'node_modules|venv|.git|__pycache__|.env|dist|build', 
        '-a', '--dirsfirst'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"هيكل المشروع - تم إنشاؤه في {datetime.now()}\n")
            f.write("======================================\n\n")
            f.write(result.stdout)
        print(f"تم إنشاء الملف باستخدام tree: {output_file}")
    else:
        raise Exception("tree غير متوفر")
        
except:
    # إذا فشل tree، نستخدم find
    try:
        result = subprocess.run([
            'find', '.', '-type', 'd', 
            '-name', 'node_modules', '-o', 
            '-name', 'venv', '-o', 
            '-name', '.git', '-o', 
            '-name', '__pycache__', '-o', 
            '-name', '.env', '-o', 
            '-name', 'dist', '-o', 
            '-name', 'build'
        ], capture_output=True, text=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"هيكل المشروع - تم إنشاؤه في {datetime.now()}\n")
            f.write("======================================\n\n")
            f.write("هيكل المشروع (مبسط):\n")
            f.write(".\n")
            for line in result.stdout.split('\n'):
                if line.strip():
                    f.write(f"|____ {line[2:]}\n")
                    
        print(f"تم إنشاء الملف باستخدام find: {output_file}")
        
    except Exception as e:
        print(f"فشل في إنشاء هيكل المشروع: {e}")