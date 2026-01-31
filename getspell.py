import re
import pymysql
all_classes = ["魔战士", "法师", "术士", "审判者", "召唤师", "炼金术师", "先知", "牧师", "德鲁伊", "吟游诗人", "游侠", "女巫", "反圣骑士", "圣骑士", "异能者", "通灵者", "催眠师", "秘学士", "唤魂师", "萨满", "血脉狂怒者"]
all_books = ['CRB', 'APG', 'ARG', 'ACG', 'UM', 'UC', 'MA', 'OA', 'UI', 'BotD', 'UW', 'PA']
spell_list = {class_name: [] for class_name in all_classes}
class Spell:
    def __init__(self, name, school, slot, level, field, spell_time, components, distance, rangee, target, effect, duration, save, sr, description, from_book):
        self.name = name
        self.school = school
        self.slot = slot
        self.level = level
        self.field = field
        self.spell_time = spell_time
        self.components = components
        self.distance = distance
        self.range = rangee
        self.target = target
        self.effect = effect
        self.duration = duration
        self.save = save
        self.sr = sr
        self.description = description
        self.from_book = from_book
for book in all_books:
    with open(book) as file:
        data = file.read()
        lines = data.splitlines()
        lines = [line for line in lines if line.strip()]
        lines = [s for s in lines if not re.fullmatch(r'[A-Za-z \']+', s)]
        index = 0
        while index < len(lines):
            name = lines[index]
            index += 1
            school = re.sub(r'学派 *', '', lines[index])
            index += 1
            slot = re.sub(r'(环位|等级) *', '', lines[index])
            classes = re.findall(r'(?:[\u4e00-\u9fff]+|术士/法师|牧师/先知) *\d', slot)
            index += 1
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '领域':
                have_field = True
                field = re.sub(r'领域 *', '', lines[index])
                index += 1
            else:
                have_field = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '施法时间':
                have_spell_time = True
                spell_time = re.sub(r'施法时间 *', '', lines[index])
                index += 1
            else:
                have_spell_time = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '成分':
                have_components = True
                components = re.sub(r'成分 *', '', lines[index])
                index += 1
            else:
                have_components = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '距离':
                have_distance = True
                distance = re.sub(r'距离 *', '', lines[index])
                index += 1
            else:
                have_distance = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '区域' or word == '范围':
                have_range = True
                rangee = re.sub(r'(区域|范围) *', '', lines[index])
                index += 1
            else:
                have_range = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '目标':
                have_target = True
                target = re.sub(r'目标 *', '', lines[index])
                index += 1
            else:
                have_target = False
            if word == '效果':
                have_effect = True
                effect = re.sub(r'效果 *', '', lines[index])
                index += 1
            else:
                have_effect = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '持续时间':
                have_duration = True
                duration = re.sub(r'持续时间 *', '', lines[index])
                index += 1
            else:
                have_duration = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '豁免':
                have_save = True
                save = re.sub(r'豁免 *', '', lines[index])
                index += 1
            else:
                have_save = False
            word = re.findall(r'[\u4e00-\u9fff]+', lines[index])[0]
            if word == '法术抗力':
                have_sr = True
                sr = re.sub(r'法术抗力 *', '', lines[index])
                index += 1
            else:
                have_save = False
            description = []
            while True:
                description.append(lines[index])
                if index == len(lines) - 1:
                    index += 1
                    break
                index += 1
                if index == len(lines) - 1:
                    description.append(lines[index])
                    index += 1
                    break
                text = re.findall(r'[\u4e00-\u9fff]+ \([A-Za-z ]+\)', lines[index])
                if book == 'ARG':
                    text = re.findall(r'[\u4e00-\u9fff]+ \([A-Za-z ]+\) \[[\u4e00-\u9fff]+\]', lines[index])
                text2 = re.findall(r'[\u4e00-\u9fff]+', lines[index + 1])
                if text == None or text == [] or text2 == None or text2 == []:
                    continue
                elif text[0] != lines[index] or text2[0] != '学派':
                    continue
                break
            for clas in classes:
                class_name, level = re.findall(r'[^\d\s]+', clas)[0], re.findall(r'\d+', clas)[0]
                if class_name == '圣武士': 
                    class_name = '圣骑士'
                if class_name == '反圣武士':
                    class_name = '反圣骑士'
                if class_name == '炼金术士':
                    class_name = '炼金术师'
                if class_name == '诗人':
                    class_name = '吟游诗人'
                if class_name == '异能师':
                    class_name = '异能者'
                if class_name == '血脉暴怒者':
                    class_name = '血脉狂怒者'
                if not class_name in all_classes and not class_name == '术士/法师' and not class_name == '牧师/先知':
                    print(class_name)
                    exit(0)
                spell = Spell(name, school, slot, level, field if have_field else None, spell_time if have_spell_time else None, components if have_components else None, distance if have_distance else None, rangee if have_range else None, target if have_target else None, effect if have_effect else None, duration if have_duration else None, save if have_save else None, sr if have_sr else None, description, book)
                if class_name == '术士/法师':
                    spell_list['法师'].append(spell)
                    spell_list['术士'].append(spell)
                elif class_name == '牧师/先知':
                    spell_list['牧师'].append(spell)
                    spell_list['先知'].append(spell)
                else:
                    spell_list[class_name].append(spell)
for class_name in all_classes:
    spell_list[class_name].sort(key=lambda p: p.level)
try:
    db = pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="pf"
    )
    print("数据库连接成功！")
except pymysql.MySQLError as e:
    print(f"连接失败：{e}")
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS spells (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    school VARCHAR(255) NOT NULL,
    slot VARCHAR(255) NOT NULL,
    class VARCHAR(255) NOT NULL,
    level INT,
    field VARCHAR(255),
    spell_time VARCHAR(255),
    components VARCHAR(255),
    distance VARCHAR(255),
    spell_range VARCHAR(255),
    target VARCHAR(255),
    effect VARCHAR(255),
    duration VARCHAR(255),
    save VARCHAR(255),
    sr VARCHAR(255),
    description VARCHAR(10000),
    from_book VARCHAR(255),
    UNIQUE KEY uk_name_class (name, class)
)
""")
for class_name in all_classes:
    for spell in spell_list[class_name]:
        description_text = "\n".join(spell.description)
        sql = """
        INSERT IGNORE INTO spells (name, school, slot, class, level, field, spell_time, components, distance, spell_range, target, effect, duration, save, sr, description, from_book)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (spell.name, spell.school, spell.slot, class_name, spell.level, spell.field, spell.spell_time, spell.components, spell.distance, spell.range, spell.target, spell.effect, spell.duration, spell.save, spell.sr, description_text, spell.from_book)
        try:
            result = cursor.execute(sql, values)
            db.commit()
            if result == 0:
                print("数据已存在，跳过插入")
            else:
                print(f"插入成功，ID: {cursor.lastrowid}")
        except pymysql.MySQLError as e:
            print(f"插入数据失败：{e}")
            print(spell.name)
            db.rollback()