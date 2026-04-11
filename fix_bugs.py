import re

def fix_base():
    with open('Leader-board/templates/base.html', 'r', encoding='utf-8') as f:
        c = f.read()
    c = c.replace('body[data-bs-theme="dark"]', '[data-bs-theme="dark"] body')
    c = c.replace('background: #0f172a;', 'background-color: #0f172a !important;')
    with open('Leader-board/templates/base.html', 'w', encoding='utf-8') as f:
        f.write(c)

def fix_dash():
    with open('Leader-board/templates/judge/dashboard.html', 'r', encoding='utf-8') as f:
        c = f.read()
    c = re.sub(r'const statusElement.*?;\n*', '', c)
    c = c.replace('|| !statusElement', '')
    c = re.sub(r'statusElement.*?;\n*', '', c)
    with open('Leader-board/templates/judge/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(c)

def fix_routes():
    with open('Leader-board/routes/judge.py', 'r', encoding='utf-8') as f:
        c = f.read()
    p1 = r'if is_judge_team_locked\(judge_profile\.id, team\.id\):\s*flash\("Scores are locked for this team and cannot be cleared\.", "warning"\)\s*return redirect\(url_for\("judge\.score_team", team_id=team\.id\)\)'
    c = re.sub(p1, '', c)
    p2 = r'if is_judge_team_locked\(judge_profile\.id, team\.id\):\s*flash\("Scores are locked for this team and cannot be edited\.", "warning"\)\s*return redirect\(url_for\("judge\.score_team", team_id=team\.id\)\)'
    c = re.sub(p2, '', c)
    c = c.replace('lock_after_save=lock_after_save,', 'lock_after_save=False,')
    c = c.replace('lock_after_save = action == "save_lock"', 'lock_after_save = False')
    c = re.sub(r'if lock_after_save:\s*flash\("Scores saved and locked successfully\.", "success"\)\s*else:\s*', '', c)
    with open('Leader-board/routes/judge.py', 'w', encoding='utf-8') as f:
        f.write(c)

fix_base()
fix_dash()
fix_routes()
