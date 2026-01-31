from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import pymysql
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'pf',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 硬编码选项（避免数据库查询）
CLASSES = [
    "魔战士", "法师", "术士", "审判者", "召唤师", "炼金术师", 
    "先知", "牧师", "德鲁伊", "吟游诗人", "游侠", "女巫", 
    "反圣骑士", "圣骑士", "异能者", "通灵者", "催眠师", 
    "秘学士", "唤魂师", "萨满", "血脉狂怒者"
]

BOOKS = ['CRB', 'APG', 'ARG', 'ACG', 'UM', 'UC', 'MA', 'OA', 'UI', 'BotD', 'UW', 'PA']

def get_db():
    return pymysql.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/spells')
def search_spells():
    """查询法术（同名自动去重）"""
    try:
        # 获取参数
        name = request.args.get('name', '').strip()
        class_ = request.args.get('class', '').strip()
        level = request.args.get('level', '').strip()
        desc = request.args.get('description', '').strip()
        books = request.args.getlist('from_book')  # 支持多选
        
        conn = get_db()
        
        # 使用窗口函数去重（MySQL 8.0+）：同名法术取第一条
        sql = """
        WITH RankedSpells AS (
            SELECT 
                name, school, slot, field, spell_time, components,
                distance, spell_range, target, effect, duration,
                save, sr, description, from_book,
                ROW_NUMBER() OVER (PARTITION BY name ORDER BY class) as rn
            FROM spells
            WHERE 1=1
        """
        params = []
        
        if name:
            sql += " AND name LIKE %s"
            params.append(f"%{name}%")
            
        if class_:
            sql += " AND class = %s"
            params.append(class_)
            
            if level:
                sql += " AND level = %s"
                params.append(int(level))
        elif level:
            # 如果没选职业但选了等级，忽略等级（或返回错误）
            pass
            
        if desc:
            sql += " AND description LIKE %s"
            params.append(f"%{desc}%")
            
        if books:
            placeholders = ','.join(['%s'] * len(books))
            sql += f" AND from_book IN ({placeholders})"
            params.extend(books)
            
        sql += """
        )
        SELECT * FROM RankedSpells
        WHERE rn = 1
        ORDER BY name
        LIMIT 50
        """
        
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            # 清理 None 值（前端处理更方便）
            for spell in results:
                for key in list(spell.keys()):
                    if spell[key] is None:
                        spell[key] = ''
            
            return jsonify({
                'success': True,
                'count': len(results),
                'data': results
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/options')
def get_options():
    """获取筛选选项"""
    return jsonify({
        'classes': CLASSES,
        'books': BOOKS,
        'levels': list(range(10))  # 0-9
    })

# 前端 HTML 模板（嵌入式，无需额外文件）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>法术查询系统</title>
    <style>
        :root {
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --bg: #f3f4f6;
            --card: #ffffff;
            --text: #1f2937;
            --text-secondary: #6b7280;
            --border: #e5e7eb;
            --radius: 8px;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text);
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--card);
            border-radius: 16px;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
            overflow: hidden;
        }
        
        .header {
            background: var(--text);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 { font-size: 2rem; margin-bottom: 8px; }
        .header p { opacity: 0.8; font-size: 0.95rem; }
        .header .author { 
            font-size: 0.8rem; 
            opacity: 0.6; 
            margin-top: 8px;
            font-style: italic;
            letter-spacing: 0.5px;
        }
        
        /* 筛选面板 */
        .filter-panel {
            padding: 24px;
            background: #f9fafb;
            border-bottom: 2px solid var(--border);
        }
        
        .filter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }
        
        .form-group label {
            display: block;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        input, select {
            width: 100%;
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            font-size: 0.95rem;
            transition: all 0.2s;
            background: white;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        
        select:disabled {
            background: #f3f4f6;
            cursor: not-allowed;
            color: #9ca3af;
        }
        
        .hint {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 4px;
        }
        
        /* 多选标签 */
        .multi-select {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 8px;
            border: 2px solid var(--border);
            border-radius: var(--radius);
            min-height: 44px;
            cursor: text;
        }
        
        .multi-select:focus-within {
            border-color: var(--primary);
        }
        
        .tag {
            background: var(--primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .tag button {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 1.1rem;
            padding: 0;
            width: 18px;
            height: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }
        
        .tag button:hover { background: rgba(255,255,255,0.2); }
        
        .search-btn {
            width: 100%;
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: var(--radius);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        
        .search-btn:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .search-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        
        /* 结果区域 */
        .results {
            padding: 24px;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .spell-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .spell-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .spell-card:hover {
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
            transform: translateY(-2px);
            border-color: var(--primary);
        }
        
        .spell-title {
            font-size: 1.25rem;
            font-weight: bold;
            color: var(--text);
            margin-bottom: 8px;
            padding-right: 60px;
        }
        
        .spell-school {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .spell-section {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #f3f4f6;
        }
        
        .spell-section-title {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
            font-weight: 600;
        }
        
        .spell-section-content {
            font-size: 0.95rem;
            color: var(--text);
            line-height: 1.5;
        }
        
        .spell-meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 12px;
        }
        
        .meta-item {
            background: #f9fafb;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.875rem;
        }
        
        .meta-label {
            color: var(--text-secondary);
            font-size: 0.75rem;
            margin-bottom: 2px;
        }
        
        .meta-value {
            color: var(--text);
            font-weight: 500;
        }
        
        .description {
            margin-top: 16px;
            padding: 12px;
            background: #f9fafb;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.6;
            color: var(--text);
            border-left: 3px solid var(--primary);
        }
        
        .empty {
            text-align: center;
            padding: 60px;
            color: var(--text-secondary);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        
        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 16px;
            border-radius: var(--radius);
            margin-bottom: 20px;
        }
        
        @media (max-width: 640px) {
            .spell-grid { grid-template-columns: 1fr; }
            .header h1 { font-size: 1.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📜 法术查询系统</h1>
            <p>Pathfinder 法术数据库</p>
            <div class="author">by WAHearer</div>
        </div>
        
        <div class="filter-panel">
            <div class="filter-grid">
                <div class="form-group">
                    <label>法术名称</label>
                    <input type="text" id="inputName" placeholder="输入法术名称..." autocomplete="off">
                </div>
                
                <div class="form-group">
                    <label>职业</label>
                    <select id="selectClass">
                        <option value="">全部职业</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>法术环位</label>
                    <select id="selectLevel" disabled>
                        <option value="">请先选择职业</option>
                    </select>
                    <div class="hint" id="levelHint">选择特定职业后可筛选环位</div>
                </div>
                
                <div class="form-group">
                    <label>来源书籍</label>
                    <div class="multi-select" id="bookSelect" onclick="toggleBookDropdown()">
                        <span style="color:#9ca3af" id="bookPlaceholder">点击选择来源...</span>
                    </div>
                </div>
            </div>
            
            <div class="form-group" style="margin-bottom:16px">
                <label>描述包含</label>
                <input type="text" id="inputDesc" placeholder="搜索描述中的关键词（如：火焰、治疗）...">
            </div>
            
            <button class="search-btn" onclick="searchSpells()" id="btnSearch">
                🔍 搜索法术
            </button>
        </div>
        
        <div class="results">
            <div class="results-header">
                <span id="resultCount">准备就绪</span>
            </div>
            <div id="spellResults"></div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let selectedBooks = [];
        
        // 字段名映射（中文标签）
        const fieldMap = {
            'school': '学派',
            'slot': '环位',
            'field': '领域',
            'spell_time': '施法时间',
            'components': '法术成分',
            'distance': '距离',
            'spell_range': '范围',
            'target': '目标',
            'effect': '效果',
            'duration': '持续时间',
            'save': '豁免',
            'sr': '法术抗力',
            'from_book': '来源'
        };
        
        // 初始化
        window.onload = async () => {
            await loadOptions();
            setupEventListeners();
            searchSpells(); // 默认加载所有
        };
        
        async function loadOptions() {
            try {
                const res = await fetch(`${API_BASE}/api/options`);
                const data = await res.json();
                
                // 填充职业
                const classSelect = document.getElementById('selectClass');
                data.classes.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c;
                    opt.textContent = c;
                    classSelect.appendChild(opt);
                });
                
                // 填充环位（0-9）
                updateLevelOptions(data.levels);
                
            } catch (err) {
                console.error('加载选项失败:', err);
            }
        }
        
        function updateLevelOptions(levels) {
            const levelSelect = document.getElementById('selectLevel');
            const currentClass = document.getElementById('selectClass').value;
            
            if (!currentClass) {
                levelSelect.disabled = true;
                levelSelect.innerHTML = '<option value="">请先选择职业</option>';
                document.getElementById('levelHint').style.display = 'block';
                return;
            }
            
            levelSelect.disabled = false;
            document.getElementById('levelHint').style.display = 'none';
            levelSelect.innerHTML = '<option value="">全部环位</option>';
            
            levels.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l;
                opt.textContent = l === 0 ? '戏法 (0)' : `${l} 环`;
                levelSelect.appendChild(opt);
            });
        }
        
        function setupEventListeners() {
            // 职业改变时更新环位选项
            document.getElementById('selectClass').addEventListener('change', (e) => {
                updateLevelOptions([0,1,2,3,4,5,6,7,8,9]);
                if (!e.target.value) {
                    document.getElementById('selectLevel').value = '';
                }
            });
            
            // 回车搜索
            document.getElementById('inputName').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') searchSpells();
            });
        }
        
        // 书籍多选模拟（简化版用prompt，完整版用自定义下拉）
        function toggleBookDropdown() {
            const books = ['CRB', 'APG', 'ARG', 'ACG', 'UM', 'UC', 'MA', 'OA', 'UI', 'BotD', 'UW', 'PA'];
            const current = selectedBooks.length > 0 ? selectedBooks.join(',') : '';
            const input = prompt(`选择来源书籍（用逗号分隔）：\\n可选：${books.join(', ')}\\n\\n当前选择：`, current);
            
            if (input !== null) {
                selectedBooks = input.split(',').map(b => b.trim()).filter(b => b);
                updateBookDisplay();
            }
        }
        
        function updateBookDisplay() {
            const container = document.getElementById('bookSelect');
            const placeholder = document.getElementById('bookPlaceholder');
            
            if (selectedBooks.length === 0) {
                container.innerHTML = '<span style="color:#9ca3af" id="bookPlaceholder">点击选择来源...</span>';
            } else {
                container.innerHTML = selectedBooks.map(book => `
                    <span class="tag">
                        ${book}
                        <button onclick="event.stopPropagation(); removeBook('${book}')">×</button>
                    </span>
                `).join('') + '<span style="color:#9ca3af;font-size:0.9rem;margin-left:auto;cursor:pointer" onclick="toggleBookDropdown()">+ 添加</span>';
            }
        }
        
        function removeBook(book) {
            selectedBooks = selectedBooks.filter(b => b !== book);
            updateBookDisplay();
        }
        
        async function searchSpells() {
            const btn = document.getElementById('btnSearch');
            const resultsDiv = document.getElementById('spellResults');
            const countDiv = document.getElementById('resultCount');
            
            btn.disabled = true;
            btn.innerHTML = '⏳ 查询中...';
            
            // 构建参数
            const params = new URLSearchParams();
            const name = document.getElementById('inputName').value;
            const cls = document.getElementById('selectClass').value;
            const level = document.getElementById('selectLevel').value;
            const desc = document.getElementById('inputDesc').value;
            
            if (name) params.append('name', name);
            if (cls) params.append('class', cls);
            if (level && cls) params.append('level', level);  // 只有选了职业才传level
            if (desc) params.append('description', desc);
            selectedBooks.forEach(b => params.append('from_book', b));
            
            try {
                const res = await fetch(`${API_BASE}/api/spells?${params}`);
                const data = await res.json();
                
                if (!data.success) throw new Error(data.error);
                
                countDiv.textContent = `找到 ${data.count} 个法术`;
                
                if (data.data.length === 0) {
                    resultsDiv.innerHTML = '<div class="empty">未找到匹配的法术</div>';
                    return;
                }
                
                resultsDiv.innerHTML = `<div class="spell-grid">${data.data.map(renderSpell).join('')}</div>`;
                
            } catch (err) {
                resultsDiv.innerHTML = `<div class="error">查询失败: ${err.message}</div>`;
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔍 搜索法术';
            }
        }
        
        function renderSpell(spell) {
            // 生成字段展示（只显示非空字段）
            const fields = ['school', 'slot', 'field', 'spell_time', 'components', 'distance', 'spell_range', 'target', 'effect', 'duration', 'save', 'sr', 'from_book']
                .filter(key => spell[key] && spell[key].toString().trim() !== '')
                .map(key => `
                    <div class="meta-item">
                        <div class="meta-label">${fieldMap[key]}</div>
                        <div class="meta-value">${escapeHtml(spell[key])}</div>
                    </div>
                `).join('');
            
            return `
                <div class="spell-card">
                    <div class="spell-school">${escapeHtml(spell.school)}</div>
                    <div class="spell-title">${escapeHtml(spell.name)}</div>
                    
                    ${fields ? `<div class="spell-meta-grid">${fields}</div>` : ''}
                    
                    ${spell.description ? `
                        <div class="description">
                            ${escapeHtml(spell.description)}
                        </div>
                    ` : ''}
                </div>
            `;
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)