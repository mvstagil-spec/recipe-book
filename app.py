import logging
import os
import re
import unicodedata
from difflib import get_close_matches
from html import escape

import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, url_for

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")
app = Flask(__name__, static_folder="images", static_url_path="/images")
CATEGORIES = ("Завтрак", "Обед", "Ужин")

PHOTO_FILES = {'Яичница': 'yaichnica', 'Омлет': 'omlet', 'Блины': 'blini', 'Оладьи': 'oladi', 'Сырники': 'syrniki', 'Гренки': 'grenki', 'Яичница с беконом': 'Yaychnitsa_s_bekonom', 'Сосиски с яйцом': 'Sosiski_s_yaytsem', 'Омлет со шпинатом и сыром': 'Omlet_so_shpinatom_i_syrom', 'Тост с авокадо и яйцом': 'Tost_s_avokado_i_yaytsem', 'Бутерброд с сыром и помидором': 'Buterbrod_s_syrom_i_pomidorom', 'Бутерброд с колбасой и огурцом': 'Buterbrod_s_kolbasoy_i_ogurtsom', 'Бутерброд с рыбой': 'Buterbrod_s_rybοi', 'Лаваш с сыром и овощами': 'Lavash_s_syrom_i_ovoshchami', 'Творог со сметаной и вареньем': 'Tvorog_so_smetanoj_i_varenjem', 'Йогурт с ягодами': 'Joghurt_s_jagodami', 'Йогурт с орехами и семечками': 'Joghurt_s_jagodami', 'Чиа с молоком и вареньем': 'Chia_s_molokom_i_varenem', 'Кефир с бананом и яблоком': 'Kefir_s_bananom_i_yablokom', 'Фрукты со сметаной': 'Frukty_so_smetanoj', 'Рис отварной': 'Ris_otvarnoj', 'Гречка': 'Grečka', 'Перловка с луком и морковью': 'Perlovka_s_lukom_i_morkovju', 'Булгур с болгарским перцем': 'bulgur_s_bolgarskim_percem', 'Рожки с томатной пастой': 'rozhi_s_tomatnoj_pastoj', 'Картофель жареный с луком': 'kartofel_zharenyj_s_lukom', 'Тушёная капуста': 'tusyonaya_kapusta', 'Борщ': 'borsh', 'Куриный суп': 'kurinyj_sup', 'Гречка с курицей': 'grechka_s_kuricej', 'Свинина с картофелем': 'svinina_s_kartofelem', 'Котлеты': 'kotlety', 'Макароны с фаршем': 'makarony_s_farshem', 'Жареное филе белой рыбы': 'zharenoe_file_beloy_ryby', 'Филе красной рыбы с укропом': 'file_krasnoj_ryby_s_ukropom', 'Гороховый суп': 'gorohovyj_sup', 'Чечевица с овощами': 'chechevitsa_s_ovoshchami', 'Фасоль в томате': 'fasol_v_tomate', 'Овощной салат': 'ovoschnoy_salat', 'Рыбный суп': 'rybnyy_sup', 'Курица в томате': 'kurica_v_tomate', 'Гуляш': 'gulyash', 'Подлива из фарша': 'podliva_iz_farsha', 'Куриное филе в сливках': 'kurinoe_file_v_slivkakh', 'Куриные бёдра с паприкой': 'kurinye_byedra_s_paprikoj', 'Куриные голени в томате': 'kurinye_goleni_v_tomate', 'Куриное филе в йогурте': 'kurinoe_file_v_yogurte', 'Куриное филе в кукурузных хлопьях': 'kurinoe_file_v_kukuruznykh_hlopyakh', 'Котлеты из говяжьего фарша': 'kotlety_iz_govyazhego_farsha', 'Котлеты из свиного фарша': 'kotlety_iz_svinogo_farsha', 'Котлеты из смешанного фарша': 'kotlety_iz_smeshannogo_farsha', 'Котлеты из куриного фарша': 'kotlety_iz_kurinogo_farsha', 'Куриная печень с луком': 'kurinaya_pechen_s_lukom', 'Говяжья печень в сметане': 'govyazhya_pechen_v_smetane', 'Куриные сердечки в сметане': 'kurinye_serdtsechki_v_smetane', 'Жареный минтай': 'zharenyj_mintaj', 'Треска в духовке': 'treska_v_duhovke', 'Лосось с брокколи': 'Losel_s_brokkoli', 'Горбуша тушёная с морковью': 'Gorbusha_tusyonaya_s_morkovyu', 'Креветки в соевом соусе': 'Krevetki_v_soevom_souse', 'Жареный кальмар': 'Zherenyj_kalmar', 'Салат с тунцом': 'Salat_s_tuncom', 'Картофель с консервированной горбушей': 'Kartofel_s_konservirovannoj_gorbushej', 'Спагетти с говяжьим фаршем': 'Spagetti_s_govyazhim_farshom', 'Перья с куриным филе': 'Perya_s_kurinym_file', 'Рожки по-флотски': 'Rozhi_po-flotski', 'Рис белый': 'Ris_belyy', 'Бурый рис с куриным фаршем': 'Buryj_ris_s_kurinym_farshom', 'Гречка с шампиньонами': 'Grechka_s_shampinjonami', 'Булгур с кабачком': 'bulgur_s_kabachkom', 'Кускус с овощами': 'kuskus_s_ovoshchami', 'Овсянка с сыром': 'ovsyanka_s_syrom', 'Овощное рагу на ужин': 'ovoschnoye_ragu_na_uzhin', 'Баклажаны в протёртых томатах': 'baklazhany_v_protyortykh_tomatax', 'Цветная капуста в сухарях': 'cvetnaya_kapusta_v_suharyah', 'Тушёная белокочанная капуста': 'tusyonaya_belokochannaya_kapusta', 'Свекла с чесноком': 'svekla_s_chesnokom', 'Тыква с тимьяном': 'tykva_s_timyanom', 'Жареный картофель на ужин': 'zharenyj_kartofel_na_uzhin', 'Фасоль с томатной пастой': 'fasol_s_tomatnoj_pastoj', 'Вешенки в сметане': 'veshenki_v_smetane', 'Белые грибы с картофелем': 'Belyye_griby_s_kartofelem', 'Салат с перепелиными яйцами': 'Salat_s_perepelinymi_yaytsami', 'Чили с консервированной фасолью': 'Chili_s_konservirovannoy_fasolyu', 'Нут с куркумой': 'Nut_s_kurkumoj', 'Салат с горошком и кукурузой': 'Salat_s_gorokhom_i_kukuruzoy', 'Солянка с маслинами': 'Solyanka_s_maslinami', 'Салат с оливками': 'Salat_s_olivkami', 'Творожная запеканка': 'Tvorozhnaya_zapekanka', 'Горячий лаваш с сыром': 'Goryachiy_lavash_s_syrom', 'Лаваш с творожным сыром': 'Lavash_s_tvorozhnym_syrom', 'Горошек с морковью': 'Goroshek_s_morkovyu'}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".avif", ".gif"}


def _photo_key(value):
    """Учитывает регистр, пробелы, дефисы, апострофы и латинские диакритики."""
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("ß", "ss").replace("ø", "o").replace("ł", "l").replace("ο", "o").replace("о", "o")
    return re.sub(r"[^a-z0-9]", "", value)


PHOTO_ALTERNATIVES = {
    "Яичница с беконом": ("eggs_with_bacon",),
    "Свекла с чесноком": ("svyekla_s_chesnokom", "svekla_s_chesnokom"),
    "Куриные бёдра с паприкой": ("kurinye_byodra_s_paprikoj", "kurinye_bedra_s_paprikoj"),
    "Жареное филе белой рыбы": ("zharenoe_file_beloj_ryby",),
    "Чиа с молоком и вареньем": ("Chia_s_molokom_i_varenem",),
}


def recipe_photo_url(recipe_name):
    """Находит фото по имени, расширению и распространенным вариантам написания."""
    stem = PHOTO_FILES.get(recipe_name)
    if not stem:
        return None
    image_dir = os.path.join(app.root_path, "images")
    if not os.path.isdir(image_dir):
        app.logger.warning("Папка с фотографиями не найдена: %s", image_dir)
        return None

    candidates = [stem, *PHOTO_ALTERNATIVES.get(recipe_name, ())]
    files = []
    for filename in os.listdir(image_dir):
        full_path = os.path.join(image_dir, filename)
        if not os.path.isfile(full_path):
            continue
        clean_filename = re.sub(r"\s*\.\s*(jpg|jpeg|png|webp|jfif|avif|gif)$", r".\1", filename, flags=re.IGNORECASE)
        basename, ext = os.path.splitext(clean_filename)
        if ext.casefold() in IMAGE_EXTENSIONS:
            files.append((filename, _photo_key(basename)))

    for desired in candidates:
        norm = _photo_key(desired)
        for filename, key in files:
            if key == norm:
                return url_for("static", filename=filename)

    # Только для диагностики: не подставляем чужую фотографию автоматически.
    known_keys = [key for _, key in files]
    near = get_close_matches(_photo_key(stem), known_keys, n=3, cutoff=0.72)
    suggestions = [name for name, key in files if key in near]
    app.logger.warning("Нет фото для «%s» (ищем: %s). Похожие файлы: %s", recipe_name, stem, suggestions)
    return None


BASE_UNIT = {"шт.", "г", "мл", "ч. л.", "ломтика", "зубчика", "щепотка", "по вкусу"}


def normalize(text):
    """Нормализация для поиска, без нечеткого совпадения подстрок."""
    return re.sub(r"\s+", " ", text.casefold().replace("ё", "е").strip())


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "Recipe book"),
        user=os.getenv("DB_USER", "postgres"),
        password=DB_PASSWORD,
    )


def find_recipes(category, user_ingredients, only_ready=False, show_all=False):
    """Учитывает ингредиенты по названиям; количество нужно только для рецептов."""
    sql = """
        SELECT r.id, r.name, r.instructions, r.cooking_time,
               i.name, i.canonical_name, i.is_staple, ri.quantity, ri.unit
        FROM recipes r
        JOIN categories c ON c.id = r.category_id
        JOIN recipe_ingredients ri ON ri.recipe_id = r.id
        JOIN ingredients i ON i.id = ri.ingredient_id
        WHERE c.name = %s
        ORDER BY r.name, r.id, i.name
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT alias, canonical_name FROM ingredient_aliases")
            aliases = {normalize(a): normalize(c) for a, c in cur.fetchall()}
            cur.execute("SELECT name, canonical_name FROM ingredients")
            for name, canonical in cur.fetchall():
                aliases[normalize(name)] = normalize(canonical or name)
            cur.execute(sql, (category,))
            rows = cur.fetchall()

    provided = {aliases.get(normalize(term), normalize(term)) for term in user_ingredients if normalize(term)}
    if not provided and not show_all:
        return []
    dishes = {}
    for recipe_id, name, instructions, minutes, ingredient, canonical, is_staple, quantity, unit in rows:
        dish = dishes.setdefault(recipe_id, {
            "name": name, "instructions": instructions or "", "minutes": minutes,
            "ingredients": [], "missing": [], "available_count": 0, "needed_count": 0, "query_matches": 0, "query_products": set()
        })
        normalized_name = normalize(canonical or ingredient)
        explicitly_matched = normalized_name in provided
        matched = is_staple or explicitly_matched
        if explicitly_matched:
            dish["query_products"].add(normalized_name)
            dish["query_matches"] = len(dish["query_products"])
        if not is_staple:
            dish["needed_count"] += 1
            if matched:
                dish["available_count"] += 1
            else:
                dish["missing"].append(ingredient)
        dish["ingredients"].append({
            "name": ingredient, "quantity": quantity, "unit": unit,
            "matched": matched, "staple": is_staple,
        })

    found = []
    for dish in dishes.values():
        # В обычном поиске достаточно хотя бы одного введенного продукта.
        # Совпадения считаются с учетом синонимов; базовые продукты сами по себе
        # не делают рецепт подходящим (если их не ввел пользователь).
        if not show_all and not (provided & dish["query_products"]):
            continue
        if only_ready and not show_all:
            if not dish["missing"]:
                found.append(dish)
        else:
            found.append(dish)
    # Вначале блюда с наибольшим числом совпадений запроса.
    # При равном числе совпадений выше блюда с меньшим числом недостающих продуктов.
    found.sort(key=lambda d: (-d["query_matches"] if not show_all else 0,
                              len(d["missing"]) != 0,
                              -d["available_count"] / max(d["needed_count"], 1),
                              len(d["missing"]), d["name"]))
    return found


def format_ingredient(item):
    qty = item["quantity"]
    unit = item["unit"] or ""
    if qty is None:
        return item["name"]
    amount = f"{qty:g}" if isinstance(qty, (float, int)) else format(qty, "f").rstrip("0").rstrip(".")
    if unit == "по вкусу":
        return f'{item["name"]} — по вкусу'
    return f'{item["name"]} — {amount} {unit}'.strip()


@app.route("/", methods=["GET", "POST"])
def index():
    category = "Завтрак"
    search_query = ""
    mode = "all"
    searched = request.method == "POST"
    show_all = False
    recipes = []
    error_message = ""
    if searched:
        category = request.form.get("category", "Завтрак")
        if category not in CATEGORIES:
            category = "Завтрак"
        mode = request.form.get("mode", "all")
        if mode not in ("all", "ready"):
            mode = "all"
        search_query = request.form.get("ingredients", "")[:1500]
        entered = [x.strip() for x in search_query.split(",") if x.strip()]
        show_all = request.form.get("action") == "show_all"
        if show_all:
            search_query = ""  # Не оставляем в поле неиспользуемый при просмотре запрос.
        try:
            recipes = find_recipes(category, entered, mode == "ready", show_all=show_all)
        except psycopg2.Error:
            app.logger.exception("Ошибка при поиске рецептов")
            error_message = "Не удалось получить рецепты. Проверьте подключение к базе данных."

    category_buttons = ""
    for name in CATEGORIES:
        checked = "checked" if name == category else ""
        category_buttons += f"""
            <label class="meal"><input type="radio" name="category" value="{name}" {checked}><span>{name}</span></label>
        """
    all_checked = "checked" if mode == "all" else ""
    ready_checked = "checked" if mode == "ready" else ""
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Кулинарная книга</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --bg: #f8fafc;
                    --surface: #ffffff;
                    --text: #0f172a;
                    --text-muted: #64748b;
                    --primary: #16a34a;
                    --primary-soft: #dcfce7;
                    --primary-dark: #15803d;
                    --accent: #fef08a;
                    --border: #e2e8f0;
                    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05);
                    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05);
                    --radius: 12px;
                }}

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    padding: 48px 20px;
                    background: var(--bg);
                    font-family: 'Inter', system-ui, -apple-system, sans-serif;
                    color: var(--text);
                    line-height: 1.5;
                }}

                .container {{
                    max-width: 720px;
                    margin: 0 auto;
                }}

                h1 {{
                    font-size: 2.25rem;
                    font-weight: 700;
                    letter-spacing: -0.025em;
                    margin: 0 0 8px;
                    color: var(--primary-dark);
                    text-align: center;
                }}

                .subtitle {{
                    color: var(--text-muted);
                    font-size: 1rem;
                    line-height: 1.6;
                    margin: 0 0 32px;
                }}

                .search-card {{
                    background: var(--surface);
                    border-radius: var(--radius);
                    padding: 24px;
                    box-shadow: var(--shadow);
                    border: 1px solid var(--border);
                    margin-bottom: 32px;
                }}

                .meals {{
                    display: flex;
                    gap: 8px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }}

                .meal {{
                    position: relative;
                    cursor: pointer;
                }}

                .meal input {{
                    position: absolute;
                    opacity: 0;
                    width: 0;
                    height: 0;
                }}

                .meal span {{
                    display: inline-block;
                    padding: 10px 18px;
                    border-radius: 999px;
                    border: 1.5px solid var(--border);
                    background: var(--surface);
                    color: var(--text);
                    font-weight: 500;
                    font-size: 0.95rem;
                    transition: all 0.15s ease;
                }}

                .meal:hover span {{
                    border-color: var(--primary);
                    background: var(--primary-soft);
                }}

                .meal input:checked + span {{
                    background: var(--primary);
                    color: white;
                    border-color: var(--primary);
                    box-shadow: 0 1px 2px rgb(22 163 74 / 0.2);
                }}

                .search-line {{
                    display: flex;
                    gap: 12px;
                    align-items: center;
                }}

                input[type="text"] {{
                    flex: 1;
                    padding: 14px 16px;
                    font-size: 1rem;
                    border: 1.5px solid var(--border);
                    border-radius: 10px;
                    outline: none;
                    background: #f8fafc;
                    transition: border-color 0.15s, box-shadow 0.15s;
                    font-family: inherit;
                }}

                input[type="text"]:focus {{
                    border-color: var(--primary);
                    background: white;
                    box-shadow: 0 0 0 3px rgb(22 163 74 / 0.15);
                }}

                button {{
                    padding: 14px 24px;
                    font-size: 1rem;
                    font-weight: 600;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    transition: background 0.15s, transform 0.1s;
                    font-family: inherit;
                    white-space: nowrap;
                }}

                button:hover {{
                    background: var(--primary-dark);
                }}

                button:active {{
                    transform: scale(0.98);
                }}

                .results {{
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }}

                .recipe-card {{
                    background: var(--surface);
                    border-radius: var(--radius);
                    padding: 20px 24px;
                    box-shadow: var(--shadow);
                    border: 1px solid var(--border);
                    transition: box-shadow 0.2s, transform 0.15s;
                }}

                .recipe-photo {{
                    display: block;
                    width: 100%;
                    max-height: 270px;
                    aspect-ratio: 16 / 9;
                    object-fit: cover;
                    border-radius: 10px;
                    margin-bottom: 18px;
                    background: var(--bg);
                }}

                .recipe-card:hover {{
                    box-shadow: var(--shadow-lg);
                    transform: translateY(-1px);
                }}

                .recipe-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    gap: 16px;
                    margin-bottom: 12px;
                }}

                .recipe-title {{
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin: 0;
                    color: var(--text);
                }}

                .badge {{
                    flex-shrink: 0;
                    padding: 6px 12px;
                    border-radius: 999px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    white-space: nowrap;
                }}

                .badge.full {{
                    background: var(--primary-soft);
                    color: var(--primary-dark);
                }}

                .badge.partial {{
                    background: #f1f5f9;
                    color: var(--text-muted);
                }}

                .ingredients-list {{
                    margin: 0 0 10px;
                    color: var(--text-muted);
                    font-size: 0.95rem;
                }}

                .ingredients-list strong {{
                    color: var(--text);
                    font-weight: 600;
                }}

                .ingredient.match {{
                    background: #fef08a;
                    color: #166534;
                    font-weight: 600;
                    padding: 1px 7px;
                    border-radius: 999px;
                }}

                .recipe-text {{
                    margin: 0;
                    color: #334155;
                    font-size: 0.95rem;
                    line-height: 1.6;
                }}

                .empty-msg {{
                    text-align: center;
                    padding: 48px 24px;
                    color: var(--text-muted);
                    background: var(--surface);
                    border-radius: var(--radius);
                    border: 1px dashed var(--border);
                    font-size: 1rem;
                }}

                .show-all-button {{
                    display: inline-block;
                    margin-top: 0;
                    padding: 9px 16px;
                    border-radius: 999px;
                    background: white;
                    color: var(--primary-dark);
                    border: 1.5px solid var(--primary);
                    font-size: 0.95rem;
                }}
                .show-all-button:hover {{
                    background: var(--primary-soft);
                }}
                .filters {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }}
                .filter-option {{ cursor:pointer; }}
                .filter-option input {{ position:absolute; opacity:0; }}
                .filter-option span {{ display:inline-block; border:1.5px solid var(--border); border-radius:999px; padding:9px 16px; font-weight:600; background:white; }}
                .filter-option input:checked + span {{ background:var(--primary-soft); border-color:var(--primary); color:var(--primary-dark); }}
                .meta {{ display:flex; align-items:center; gap:10px; color:var(--text-muted); font-size:0.9rem; margin-bottom:12px; }}
                .note {{ color:var(--text-muted); font-size:0.82rem; margin-top:10px; }}
                .stats {{ margin:0 0 12px; color:var(--text-muted); }}
                @media (max-width: 640px) {{
                    body {{
                        padding: 32px 16px;
                    }}
                    .search-line {{
                        flex-direction: column;
                        align-items: stretch;
                    }}
                    button {{
                        width: 100%;
                    }}
                    .recipe-header {{
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 8px;
                    }}
                }}
            </style>
    </head>
    <body>
      <div class="container">
        <h1>Кулинарная книга</h1>
        <p class="subtitle">Постоянно ломаете голову, что сегодня приготовить? Наш сервис решает эту проблему! Мы предлагаем уникальную кулинарную книгу, которая всегда будет у вас под рукой, и вы с лёгкостью сможете подобрать вариант сегодняшнего блюда на основе имеющихся продуктов.</p>
        <div class="search-card">
          <form method="POST">
            <div class="meals">{category_buttons}</div>
            <div class="search-line">
              <input type="text" name="ingredients" value="{escape(search_query, quote=True)}" placeholder="Например: яйцо, молоко, сыр" autocomplete="off">
              <button type="submit" name="action" value="search">Найти</button>
            </div>
            <div class="filters">
              <label class="filter-option"><input type="radio" name="mode" value="all" {all_checked}><span>Все рецепты</span></label>
              <label class="filter-option"><input type="radio" name="mode" value="ready" {ready_checked}><span>Без покупок</span></label>
              <button class="show-all-button" type="submit" name="action" value="show_all">Показать все рецепты</button>
            </div>
          </form>
        </div>
        <div class="results">
    """
    if error_message:
        html += f'<div class="empty-msg">{escape(error_message)}</div>'
    elif searched:
        html += f'<p class="stats">Найдено рецептов: {len(recipes)}</p>'
        if not recipes:
            html += '<div class="empty-msg">Подходящих рецептов не найдено. Попробуйте другие продукты или нажмите «Показать все рецепты».</div>'
        for recipe in recipes:
            parts = []
            for ingredient in recipe["ingredients"]:
                item_text = escape(format_ingredient(ingredient))
                css_class = 'ingredient match' if ingredient['matched'] else 'ingredient'
                parts.append(f'<span class="{css_class}">{item_text}</span>')
            photo_url = recipe_photo_url(recipe["name"])
            photo_html = (f'<img class="recipe-photo" src="{escape(photo_url, quote=True)}" '
                          f'alt="{escape(recipe["name"], quote=True)}" loading="lazy">') if photo_url else ""
            minutes = f'⏱ Примерно {recipe["minutes"]} мин.' if recipe['minutes'] else 'Время не указано'
            html += f"""
              <article class="recipe-card">
                {photo_html}
                <div class="recipe-header"><h2 class="recipe-title">{escape(recipe['name'])}</h2></div>
                <div class="meta">{escape(minutes)}</div>
                <p class="ingredients-list"><strong>Состав (ориентировочно на 2 порции):</strong> {', '.join(parts)}</p>
                <p class="recipe-text">{escape(recipe['instructions'])}</p>
              </article>
            """
    html += """
        </div>
      </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
