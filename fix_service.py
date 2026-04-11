import re
import os

def fix():
    with open('Leader-board/services/judge_scoring_service.py', 'r', encoding='utf-8') as f:
        c = f.read()

    p1 = r'if existing_rows and any\(bool\(row\.is_locked\) for row in existing_rows\):\n\s*raise ValueError\("Scores are locked for this team and cannot be edited\."\)\n'
    c = re.sub(p1, '', c)
    
    p2 = r'if any\(bool\(row\.is_locked\) for row in rows_to_lock\):\n\s*raise ValueError\("Scores are already locked for this team\."\)\n'
    c = re.sub(p2, '', c)
    
    with open('Leader-board/services/judge_scoring_service.py', 'w', encoding='utf-8') as f:
        f.write(c)

    # Just ensure no is_locked flash happens in judge.py either
    with open('Leader-board/routes/judge.py', 'r', encoding='utf-8') as f:
        c2 = f.read()
    c2 = re.sub(r'except ValueError as exc:\n\s*flash\(str\(exc\), "warning"\)\n', 'except ValueError as exc:\n                flash(str(exc), "warning")\n', c2)
    # Actually just removed the raise from judge_scoring_service.py. That's enough.

fix()
