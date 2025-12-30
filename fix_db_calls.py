#!/usr/bin/env python3
"""
Script to convert remaining conn.execute() calls to execute_query() calls in app.py
This handles the PostgreSQL cursor conversion systematically
"""

import re
import sys

def convert_conn_execute_calls(file_path):
    """Convert conn.execute() calls to execute_query() calls"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern 1: conn.execute('query').fetchone()
    pattern1 = r"conn\.execute\(\s*'''(.*?)'''\s*\)\.fetchone\(\)"
    replacement1 = r"execute_query('''\1''', fetch_one=True)"
    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    
    # Pattern 2: conn.execute('query', [params]).fetchone()
    pattern2 = r"conn\.execute\(\s*'''(.*?)'''\s*,\s*(\[.*?\])\s*\)\.fetchone\(\)"
    replacement2 = r"execute_query('''\1''', \2, fetch_one=True)"
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # Pattern 3: conn.execute('query').fetchall()
    pattern3 = r"conn\.execute\(\s*'''(.*?)'''\s*\)\.fetchall\(\)"
    replacement3 = r"execute_query('''\1''', fetch_all=True)"
    content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)
    
    # Pattern 4: conn.execute('query', [params]).fetchall()
    pattern4 = r"conn\.execute\(\s*'''(.*?)'''\s*,\s*(\[.*?\])\s*\)\.fetchall\(\)"
    replacement4 = r"execute_query('''\1''', \2, fetch_all=True)"
    content = re.sub(pattern4, replacement4, content, flags=re.DOTALL)
    
    # Pattern 5: Simple execute without fetch (for INSERT/UPDATE/DELETE)
    pattern5 = r"conn\.execute\(\s*'''(.*?)'''\s*,\s*(\[.*?\])\s*\)"
    replacement5 = r"execute_query('''\1''', \2)"
    content = re.sub(pattern5, replacement5, content, flags=re.DOTALL)
    
    # Pattern 6: Simple execute without params
    pattern6 = r"conn\.execute\(\s*'''(.*?)'''\s*\)"
    replacement6 = r"execute_query('''\1''')"
    content = re.sub(pattern6, replacement6, content, flags=re.DOTALL)
    
    # Fix parameter placeholders from ? to %s for PostgreSQL
    content = content.replace("WHERE email = %s'", "WHERE email = %s'")
    content = content.replace("WHERE id = %s'", "WHERE id = %s'")
    content = re.sub(r'(\WWHERE\s+\w+\s*=\s*)\?', r'\1%s', content)
    content = re.sub(r'(\WAND\s+\w+\s*=\s*)\?', r'\1%s', content)
    content = re.sub(r'(\WOR\s+\w+\s*=\s*)\?', r'\1%s', content)
    content = re.sub(r'(VALUES\s*\([^)]*)\?', r'\1%s', content)
    
    return content

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_db_calls.py <app.py path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    converted_content = convert_conn_execute_calls(file_path)
    
    with open(file_path, 'w') as f:
        f.write(converted_content)
    
    print("Conversion completed!")
