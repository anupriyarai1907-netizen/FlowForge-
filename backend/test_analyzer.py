
from analyzer import analyze_project

with open("sample.py", "r", encoding="utf-8") as file:
    python_code = file.read()

with open("sample.sql", "r", encoding="utf-8") as file:
    sql_code = file.read()

result = analyze_project(python_code, sql_code)

print(result)
