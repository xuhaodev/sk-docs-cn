import os
import re

def clean_markdown_headers(directory_path):
    """
    删除指定目录下所有Markdown文件中的头部YAML元数据（两个---之间的内容）
    
    参数:
        directory_path: 包含Markdown文件的目录路径
    """
    # 编译一个正则表达式来匹配两个---之间的内容（包括这两行）
    header_pattern = re.compile(r'^---\n.*?---\n', re.DOTALL | re.MULTILINE)
    
    # 统计处理文件数和修改文件数
    total_files = 0
    modified_files = 0
    
    # 遍历目录中的所有文件
    for filename in os.listdir(directory_path):
        if filename.endswith('.md'):
            file_path = os.path.join(directory_path, filename)
            total_files += 1
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # 使用正则表达式替换头部
            new_content = header_pattern.sub('', content)
            
            # 如果内容有变化，写回文件
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                modified_files += 1
                print(f"已清理文件: {filename}")
    
    print(f"\n处理完成! 共处理 {total_files} 个Markdown文件，其中 {modified_files} 个文件被修改。")

if __name__ == "__main__":
    # 获取当前脚本所在的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 调用函数处理当前目录下的文件
    clean_markdown_headers(current_dir)
