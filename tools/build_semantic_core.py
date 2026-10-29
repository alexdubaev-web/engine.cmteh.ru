#!/usr/bin/env python3
"""Build the auditable semantic research dataset from the October Wordstat snapshot."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notes/2026-10-12-wordstat-research.json"
PRODUCTS = ROOT / "data/products.json"
ARTICLES = ROOT / "data/articles.py"
SEO_STATE = ROOT / "data/seo-state.json"
OUT = ROOT / "seo/semantic-core"
SERP_SOURCE = OUT / "serp-research.json"
CURATED_SOURCE = OUT / "curated-decisions.json"
OUTPUT_NAMES = ["core.json", "keywords.csv", "observations.csv", "excluded.csv", "page-map.csv", "measurement-queue.csv", "coverage.json"]
# Only these three compact variants were explicitly checked in the historical
# study; do not infer aliases by generally deleting punctuation.
OBSERVED_LITERAL_ALIASES = {"2601004010": "260100-4010", "2601006010": "260100-6010", "72060435": "7206-0435"}

def norm(s: str) -> str:
    value=" ".join(s.casefold().split()).strip()
    # Wordstat's outer quote operator changes its metric, not the semantic root.
    if len(value)>=2 and value[0]==value[-1]=='"':
        value=value[1:-1].strip()
    return value

def digest(path: Path) -> str:
    # Hash text input independent of Windows checkout EOL conversion. The
    # generated files are LF and the semantic content is unchanged by CRLF.
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

def csv_bytes(rows, fields):
    import io
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k: "" if row.get(k) is None else row.get(k, "") for k in fields})
    return f.getvalue().encode("utf-8")

def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

def parsed_row(raw, codes=()):
    # Wordstat accessibility snapshot wraps rows in a quoted UI locator; the final
    # integer token is the displayed count. Header rows have no such token.
    text = raw.strip()
    if text.startswith('- row '):
        text = text[6:].strip()
    if len(text) >= 2 and text[0] == text[-1] == '"':
        text = text[1:-1]
    # A displayed count is either one integer token or correctly grouped
    # thousands (1 234). Never greedily absorb a preceding numeric SKU.
    m = re.search(r"\s(\d{1,3}(?:[ \u00a0\u202f]\d{3})*|\d{1,6})\s*$", text)
    if not m:
        if re.search(r"\s\d{7,}\s*$", text):
            return text.strip(), None, "ambiguous_terminal_number"
        return text.strip(), None, "unparsed_header_or_no_count"
    q = text[:m.start()].strip()
    if len(q) >= 2 and q[0] == q[-1] == '"':
        q = q[1:-1]
    token = m.group(1)
    n = int(re.sub(r"\D", "", token))
    # Large terminal digit strings are much more likely identifiers than a
    # count; preserve the row for manual review rather than manufacturing data.
    if len(re.sub(r"\D", "", token)) > 6 or q.strip() == "":
        return text.strip(), None, "ambiguous_terminal_number"
    return q, n, "rightmost_grouped_count"

def catalog_code_hit(text, codes):
    n = norm(text)
    for code in sorted(codes, key=len, reverse=True):
        if re.search(r"(?<![\w])" + re.escape(norm(code)) + r"(?![\w])", n):
            return code
    for alias, code in OBSERVED_LITERAL_ALIASES.items():
        if code in codes and re.search(r"(?<![\w])" + re.escape(alias) + r"(?![\w])", n):
            return code
    return None

LEXICAL_ROOTS = (
    "форсун", "инжектор", "тнвд", "насос", "распылител", "клапан", "регулятор", "ремкомплект",
    "топливн", "аппаратур", "запчаст", "diesel", "common", "rail", "scv", "imv", "hpv",
    "bosch", "бош", "delphi", "делфи", "denso", "денсо", "vdo", "vitesco", "siemens",
    "john", "deere", "джон", "дир", "куп", "заказ", "цен", "стоим", "налич", "каталожн",
    "артикул", "номер", "код", "подбор", "подобрат", "маркиров", "схем", "подключен", "замен",
    "как", "почему", "что", "это", "такое", "для", "провер", "проблем", "завод", "запуск",
    "холодн", "дым", "работ", "ошибк", "список", "заказ", "нов", "оригинал", "топлив", "двигател",
    "детал", "купить", "насос-форсун", "насос", "дизел", "впрыск", "тнвд", "комплект",
)

def unknown_query_tokens(text, code=None):
    n=norm(text)
    if code:
        n=re.sub(r"(?<![\w])"+re.escape(norm(code))+r"(?![\w])"," ",n)
        for alias,canonical in OBSERVED_LITERAL_ALIASES.items():
            if canonical == code:
                n=re.sub(r"(?<![\w])"+re.escape(norm(alias))+r"(?![\w])"," ",n)
    # Any digit after removing a catalog SKU is an unverified model/code.
    if re.search(r"\d",n): return ["<number/model>"]
    tokens=re.findall(r"[a-zа-яё]+",n)
    return [t for t in tokens if not any(t.startswith(root) for root in LEXICAL_ROOTS)]

def article_records():
    text = ARTICLES.read_text(encoding="utf-8")
    slugs = re.findall(r"['\"]slug['\"]\s*:\s*['\"]([^'\"]+)['\"]", text)
    return [{"slug": s, "url": f"/articles/{s}/", "status": "published"} for s in slugs]

def route_query(text, code, by_code, page_map, categories, brand_category_pairs):
    n = norm(text)
    unknown=unknown_query_tokens(text,code)
    if unknown:
        return "", "manual_review", "Неизвестное уточнение ("+", ".join(unknown[:4])+") требует проверки по каталогу; посадочная страница не назначается автоматически"
    informational = any(x in n for x in ("как ", "почему ", "что такое", "что это", "для чего", "маркировк", "подобрать", "подбор", "номер ", "кодирован", "прописать", "проверить", "замена ", "заводится", "запускается", "дымит", "список ", "схема", "подключен", "программирован"))
    if code and informational:
        # Preserve the product number as evidence but route a how-to task to content.
        code_for_route = None
    else:
        code_for_route = code
    if code_for_route:
        p = by_code[code_for_route]
        demanded = "other" if "ремкомплект" in n else "nozzles" if "распылител" in n else "valves" if "клапан" in n or "регулятор" in n else "injectors" if "форсун" in n or "инжектор" in n else "pumps" if "тнвд" in n or "насос" in n else None
        if demanded and demanded != p.get("category"):
            return "", "manual_review", "Уточняющий тип запроса не совпадает с категорией номера; подтверждённой пары нет"
        if p["id"].casefold()=="re543262" and ("тнвд" in n or "высокого давления" in n):
            return "", "manual_review", "Для RE543262 нельзя утверждать тип ТНВД или высокое давление без точного технического подтверждения"
        return f"product:{p['id']}", "catalog_match", "Точное соответствие каталожному номеру"
    # Component specificity matters: a nozzle or valve is not the injector assembly.
    if "насос-форсун" in n or "насос форсун" in n:
        return "", "manual_review", "Смешанный термин «насос-форсунка» требует ручной привязки к типу товара"
    if "ремкомплект" in n:
        category = "other"
    elif "распылител" in n:
        category = "nozzles"
    elif "клапан" in n or "регулятор" in n:
        category = "valves"
    elif "форсун" in n or "инжектор" in n:
        category = "injectors"
    elif "тнвд" in n or "насос" in n:
        category = "pumps"
    elif "топливные запчасти" in n:
        category = "other"
    else:
        category = None
    if informational:
        if "схем" in n or "подключен" in n or "программирован" in n or "самостоятельн" in n or "замена " in n or "заменить" in n:
            hub = "category:injectors" if "форсун" in n else "category:valves" if "клапан" in n or "scv" in n else f"category:{category or 'pumps'}"
            return "proposed:technical-instruction", "proposed_article", f"Тема инструкции по схеме, замене или настройке требует отдельной проверки; внутренний раздел: {hub}"
        if any(x in n for x in ("заводится", "запускается", "холодн")):
            target = "article:dizel-ploho-zavoditsya-na-holodnuyu"
        elif "список" in n or "для заказа" in n:
            target = "article:spisok-zapchastey-dlya-zakaza"
        elif "распылител" in n or ("форсун" in n and "комплект" in n):
            target = "article:forsunka-ili-raspylitel"
        elif "тнвд" in n or "насос" in n:
            target = "article:tnvd-pered-zakazom"
        elif any(x in n for x in ("артикул", "номер", "подбор", "маркировк")):
            target = "article:podbor-po-artikulu"
        else:
            slug = "kodirovanie-forsunok" if any(x in n for x in ("кодирован", "прописать")) else "klapan-scv" if "scv" in n else "diagnostika-toplivnoy-sistemy"
            hub = "category:injectors" if "форсун" in n else "category:valves" if "клапан" in n or "scv" in n else f"category:{category or 'other'}"
            return f"proposed:{slug}", "proposed_article", f"Тема для проверки редактором; внутренний раздел: {hub}"
        return target, "existing_article", "Существующая статья отвечает на указанную задачу"
    if category:
        aliases={"bosch":("bosch","бош"),"delphi":("delphi","делфи"),"denso":("denso","денсо"),"john deere":("john deere","джон дир","джон дир"),"vdo":("vdo","vitesco","siemens")}
        for brand, terms in aliases.items():
            if any(term in n for term in terms) and (brand,category) not in brand_category_pairs:
                return "", "manual_review", "Для указанной пары бренд/тип нет подтверждённой позиции текущего каталога"
        if "клапанов" in n and any(d in n for d in ("2 клапан", "4 клапан", "8 клапан", "16 клапан", "двигател")):
            return "", "manual_review", "Количество клапанов двигателя не задаёт тип топливной детали"
        if category == "injectors" and any(term in n for term in ("bosch", "бош")):
            return "category:injectors/bosch", "existing_category", "Существующая страница Bosch-форсунок соответствует подтверждённой паре бренд/тип"
        if "топливная аппаратура" in n and not any(x in n for x in ("купить", "цена", "заказать")):
            if re.search(r"\b(москва|санкт-петербург|воронеж|екатеринбург|новосибирск|челябинск|тюмень|барнаул|ногинск|доставка|дастер|форд|транзит|фольксваген|ниссан|камаз|мтз|юмз|ямз|д245|дизель|механическ|электронн|тепловоз|экскаватор|трактор)\b",n):
                return "", "manual_review", "Уточнение требует подтверждения ассортимента, географии или совместимости; отдельной страницы нет"
            return "page:home", "existing_home", "Широкая тема ассортимента; главная страница магазина"
        target = f"category:{category if category in categories else 'other'}"
        return target, "existing_category", "Покупательский запрос о типе детали; посадочная страница соответствует существующему каталогу"
    if "топливная аппаратура" in n:
        if re.search(r"\b(москва|санкт-петербург|воронеж|екатеринбург|новосибирск|челябинск|тюмень|барнаул|ногинск|доставка|дастер|форд|транзит|фольксваген|ниссан|камаз|мтз|юмз|ямз|д245|дизель|механическ|электронн|тепловоз|экскаватор|трактор|видео|какая|сколько|купить|цена|оборудование|участок)\b",n):
            return "", "manual_review", "Дополнительное уточнение не подтверждает товар или посадочную страницу текущего каталога"
        return "page:home", "existing_home", "Широкая тема ассортимента; главная страница магазина"
    if ("доставк" in n or "оплат" in n or "как заказать" in n) and any(p["target_id"]=="page:delivery" for p in page_map):
        return "page:delivery", "existing_support", "Вопрос об оформлении или доставке; существующая служебная страница"
    if any(x in n for x in ("купить", "заказать", "где купить")):
        return "page:catalog", "existing_catalog", "Покупательский запрос об ассортименте или оформлении заказа"
    return "", "manual_review", "Формулировка не позволяет надёжно выбрать товар, тип или страницу"

def classify(text, products, codes):
    n = norm(text)
    if any(x in n for x in ("бензинов", "газовые форсун", "форсунка омывателя", "омывател", "ремонт тнвд", "ремонт форсун", "ремонт топливн", "стенд для проверки", "стенд проверки", "ваканси", "работа механик")):
        return "excluded", "Неподходящая услуга, работа или другой тип форсунки, даже если рядом указан номер"
    if re.search(r"\b(bmw|бмв|toyota|тойота|kamaz|камаз|cummins|камминз|volvo|вольво|scania|скания|caterpillar|катерпиллар|mercedes|мерседес|isuzu|исузу|iveco|ивеко|маз|урал|лада|lada|ford|форд|duster|дастер|volkswagen|фольксваген|nissan|ниссан|мтз|юмз|ямз|д245|тепловоз|экскаватор)\b",n):
        return "review", "Модельная применимость не подтверждена каталогом для этой формулировки"
    if catalog_code_hit(n, codes):
        return "commercial", "Совпадение буквального номера каталога; тип и задача дополнительно проверяются при маршрутизации"
    if re.search(r"(?<![\w])[0-9]{6,}(?![\w])",n) or re.search(r"\b0\s+\d{3}\s+\d{3}(?:\s+\d{3})?\b",n):
        return "review", "Номер не совпал с текущим каталогом; неизвестный артикул не подменяется общей категорией"
    if "опрыскивател" in n:
        return "review", "Применимость топливной детали к двигателю опрыскивателя нужно подтвердить по SKU"
    if re.search(r"(ремонт|ваканси|работ|обучени|курс|стенд|омывател|мойк|автомойк|распылител\w* для растений|пистолет|шланг|ремень|натяжител|belt|tensioner)", n):
        return "excluded", "Не относится к покупке деталей текущего ассортимента"
    if any(x in n for x in ("камаз", "kamaz", "камминз", "cummins", "volvo", "вольво", "scania", "скания", "caterpillar", "катерпиллар", "mercedes", "мерседес", "isuzu", "исузу", "iveco", "ивеко", "маз", "урал")):
        return "review", "Указана техника вне подтверждённой привязки к SKU; применимость вручную не подтверждена"
    if "ремкомплект" in n:
        return "review", "Комплект требует проверки состава и применимости; общий комплект не считается ассортиментной категорией"
    if "насос-форсун" in n or "насос форсун" in n:
        return "review", "Смешанный термин «насос-форсунка» требует ручной привязки к типу товара"
    if any(w in n for w in ("как ", "почему ", "что такое", "маркировк", "подобрать", "подбор", "номер форсун", "номер тнвд", "кодирован", "прописать форсун", "проверить клапан", "замена распылителя", "заводится", "запускается", "дымит")):
        return "editorial", "Информационный запрос для покупателей деталей"
    if any(w in n for w in ("форсун", "тнвд", "насос", "распылител", "клапан", "топливн", "ремкомплект", "запчаст", "common rail")):
        return "commercial", "Релевантная категория/тип детали; проверить ассортимент"
    return "review", "Недостаточно оснований для автоматической привязки"

def build():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    products = json.loads(PRODUCTS.read_text(encoding="utf-8"))
    articles = article_records()
    seo_state = json.loads(SEO_STATE.read_text(encoding="utf-8"))
    brand_category_pairs={(p.get("brand","").casefold(),p.get("category","")) for p in products}
    brand_category_display={(p.get("brand",""),p.get("category","")) for p in products}
    serp = json.loads(SERP_SOURCE.read_text(encoding="utf-8")) if SERP_SOURCE.exists() else None
    curated=json.loads(CURATED_SOURCE.read_text(encoding="utf-8")) if CURATED_SOURCE.exists() else None
    curated_list=(curated or {}).get("decisions",[])
    curated_by_query={norm(x["query"]):(f"cd-{i:03d}",x) for i,x in enumerate(curated_list,1)}
    codes = {str(c) for p in products for c in p.get("codes", [])}
    by_code = {str(c): p for p in products for c in p.get("codes", [])}
    observations, excluded, parents = [], [], []
    for qi, q in enumerate(source["queries"], 1):
        parent_id = f"ws-2026-10-12-q{qi:03d}"
        match = q.get("match_type", "")
        quoted = "кавыч" in norm(match) or '"' in q.get("query", "")
        metric = "quoted_total" if quoted else "broad_total"
        parents.append({"observation_id": parent_id + "-total", "query_id": parent_id, "query": q["query"], "original_query": q["query"], "normalized_query": norm(q["query"]), "raw_row": "", "row_index": 0, "value": q.get("total"), "metric_type": metric, "period": q.get("period", ""), "region": q.get("region", ""), "devices": q.get("devices", ""), "source": q.get("source", ""), "source_query_index": qi, "classification": "parent_total", "reason": "Значение над таблицей исходного исследования"})
        for ri, raw in enumerate(q.get("rows", []), 1):
            phrase, value, parse_status = parsed_row(raw, codes)
            cat, reason = classify(phrase, products, codes)
            curated_match=curated_by_query.get(norm(phrase))
            curated_id=""
            if curated_match:
                curated_id,decision=curated_match
                if decision["action"] in {"accept","review","exclude"}:
                    cat={"accept":"curated_accept","review":"review","exclude":"excluded"}[decision["action"]]
                    reason=decision.get("rationale",reason)
            if parse_status == "unparsed_header_or_no_count":
                cat, reason = "unparsed_header", "Строка интерфейса без числового наблюдения"
            row = {"observation_id": f"{parent_id}-r{ri:03d}", "query_id": parent_id, "parent_query": q["query"], "original_query": phrase, "normalized_query": norm(phrase), "raw_row": raw, "row_index": ri, "value": value, "parse_status": parse_status, "metric_type": "legacy_row_broad_under_quoted_parent" if quoted else "broad_row", "parent_metric_type": metric, "period": q.get("period", ""), "region": q.get("region", ""), "devices": q.get("devices", ""), "source": q.get("source", ""), "source_query_index": qi, "classification": cat, "reason": reason, "curated_decision_id":curated_id}
            if value is None and parse_status == "ambiguous_terminal_number":
                row["classification"] = "review"
                row["reason"] = "Последний числовой фрагмент нельзя надёжно отделить от формулировки запроса"
            observations.append(row)
            if row["classification"] == "excluded": excluded.append({"observation_id": row["observation_id"], "query": phrase, "normalized_query": norm(phrase), "value": value, "period": row["period"], "reason": row["reason"], "source_query_id": parent_id})
    observations = parents + observations

    # One mapping row per sellable SKU and supported category/brand landing page.
    page_map = []
    brand_urls = {"Bosch":"bosch", "Delphi":"delphi", "Denso":"denso", "John Deere":"john-deere", "VDO / Vitesco (Aumovio)":"vdo"}
    for p in products:
        brand=p.get("brand", "")
        page_map.append({"target_id": f"product:{p['id']}", "target_type": "existing_product", "url": f"/catalog/{p['id']}/", "sku": p["sku"], "owned_codes": "|".join(p.get("codes", [])), "brand": brand, "category": p.get("category", ""), "secondary_links": f"/category/{p.get('category','')}/|/brands/{brand_urls.get(brand, norm(brand).replace(' ', '-'))}/", "status": "active"})
    cats = sorted({p.get("category", "") for p in products})
    brands = sorted({p.get("brand", "") for p in products})
    if "/" in seo_state:
        page_map.append({"target_id":"page:home","target_type":"existing_home","url":"/","sku":"","owned_codes":"","brand":"","category":"","secondary_links":"","status":"active"})
    if "/catalog/" in seo_state:
        page_map.append({"target_id":"page:catalog","target_type":"existing_catalog","url":"/catalog/","sku":"","owned_codes":"","brand":"","category":"","secondary_links":"","status":"active"})
    for path, target_id in (("/delivery/","page:delivery"),("/contacts/","page:contacts"),("/about/","page:about")):
        if path in seo_state:
            page_map.append({"target_id":target_id,"target_type":"existing_support","url":path,"sku":"","owned_codes":"","brand":"","category":"","secondary_links":"","status":"active"})
    for cat in cats:
        page_map.append({"target_id": f"category:{cat}", "target_type": "existing_category", "url": f"/category/{cat}/", "sku": "", "owned_codes": "", "brand": "", "category": cat, "secondary_links": "", "status": "active"})
    if "/category/injectors/bosch/" in seo_state:
        bosch_injectors = [p for p in products if p.get("brand", "").casefold() == "bosch" and p.get("category") == "injectors"]
        page_map.append({"target_id": "category:injectors/bosch", "target_type": "existing_category", "url": "/category/injectors/bosch/", "sku": "|".join(sorted(p["sku"] for p in bosch_injectors)), "owned_codes": "", "brand": "Bosch", "category": "injectors", "secondary_links": "/category/injectors/|/brands/bosch/", "status": "active"})
    for brand in brands:
        page_map.append({"target_id": f"brand:{brand}", "target_type": "existing_brand", "url": f"/brands/{brand_urls.get(brand, norm(brand).replace(' ', '-'))}/", "sku": "", "owned_codes": "", "brand": brand, "category": "", "secondary_links": "", "status": "active"})
    for a in articles:
        page_map.append({"target_id": f"article:{a['slug']}", "target_type": "existing_article", "url": a["url"], "sku": "", "owned_codes": "", "brand": "", "category": "", "secondary_links": "", "status": a["status"]})

    active, candidate, review = [], [], []
    excluded_before={norm(x["query"]) for x in excluded}
    evidence_by_phrase=defaultdict(list)
    phrase_text={}
    for obs in observations:
        phrase=obs.get("original_query") or obs.get("query") or ""
        if not phrase or obs.get("parse_status")=="unparsed_header_or_no_count":
            continue
        key=norm(phrase)
        phrase_text.setdefault(key,phrase)
        evidence_by_phrase[key].append(obs)
    for key, evidence in sorted(evidence_by_phrase.items()):
        phrase=phrase_text[key]
        kind, reason = classify(phrase, products, codes)
        curated_match=curated_by_query.get(key)
        decision_id,decision=curated_match if curated_match else ("",None)
        if decision and decision["action"]=="exclude":
            if key not in excluded_before:
                excluded.append({"observation_id":evidence[0]["observation_id"],"query":phrase,"normalized_query":key,"value":None,"period":"","reason":decision.get("rationale","Curated exclusion"),"source_query_id":evidence[0].get("query_id","")})
                excluded_before.add(key)
            continue
        if kind == "excluded" and not decision:
            if key not in excluded_before:
                excluded.append({"observation_id":evidence[0]["observation_id"],"query":phrase,"normalized_query":key,"value":None,"period":"","reason":reason,"source_query_id":evidence[0].get("query_id","")})
                excluded_before.add(key)
            continue
        codehit = catalog_code_hit(phrase, codes)
        if decision and decision["action"]=="accept":
            path=decision.get("targetPath")
            page=next((p for p in page_map if p["url"]==path),None) if path else None
            if page:
                target,target_type,route_reason=page["target_id"],page["target_type"],decision.get("rationale","")
            elif decision.get("needsContentTopic"):
                target,target_type,route_reason=f"proposed:curated-{decision_id}","proposed_article",decision.get("needsContentTopic","")
            else:
                target,target_type,route_reason=route_query(phrase,codehit,by_code,page_map,cats,brand_category_pairs)
        else:
            target,target_type,route_reason=route_query(phrase,codehit,by_code,page_map,cats,brand_category_pairs)
        if (decision and decision["action"]=="review") or target_type=="manual_review" or kind=="review":
            review.append({"query":phrase,"normalized_query":key,"reason":decision.get("rationale",reason if kind=="review" else route_reason) if decision else reason if kind=="review" else route_reason,"needs_content_topic":decision.get("needsContentTopic","") if decision else "","curated_decision_id":decision_id,"evidence_ids":"|".join(x["observation_id"] for x in evidence)})
            continue
        if target_type=="proposed_article":
            slug=target.split(":",1)[1]
            hub = "category:injectors" if "форсун" in norm(phrase) else "category:valves" if "клапан" in norm(phrase) or "scv" in norm(phrase) else f"category:{'pumps' if 'тнвд' in norm(phrase) or 'насос' in norm(phrase) else 'other'}"
            proposal_url=decision.get("needsContentTopic") and f"/articles/proposed-{decision_id}/" if decision else f"/articles/proposed-{slug}/"
            if target not in {p["target_id"] for p in page_map}:
                page_map.append({"target_id":target,"target_type":"proposed_article","url":proposal_url,"sku":"","owned_codes":"","brand":"","category":"","secondary_links":next(p["url"] for p in page_map if p["target_id"]==hub),"status":"proposed"})
            target_url=proposal_url
            secondary_link=next(p["url"] for p in page_map if p["target_id"]==hub)
        else:
            target_url=next(p["url"] for p in page_map if p["target_id"]==target)
            secondary_link=""
        numeric=[x for x in evidence if x.get("value") is not None]
        one_value=numeric[0]["value"] if len(numeric)==1 else None
        one_metric=numeric[0]["metric_type"] if len(numeric)==1 else "multiple_observations" if numeric else "unmeasured"
        priority="P1" if isinstance(one_value,int) and one_value>=100 else "P2" if isinstance(one_value,int) and one_value>0 else "P3" if one_value==0 else "unranked_multiple_or_missing"
        active.append({"keyword_id":f"kw-{len(active)+1:05d}","query":phrase,"normalized_query":key,"intent":"informational" if target_type in {"existing_article","proposed_article"} else "commercial","primary_target":target,"target_url":target_url,"target_status":"proposed" if target_type=="proposed_article" else "existing","secondary_link":secondary_link,"measurement_status":"observed","observed_value":one_value,"metric_type":one_metric,"period":numeric[0]["period"] if len(numeric)==1 else "","evidence_count":len(evidence),"evidence_ids":"|".join(x["observation_id"] for x in evidence),"curated_decision_id":decision_id,"priority":priority,"priority_basis":"Основание по одному значению только если для формулировки есть ровно одно числовое наблюдение; для нескольких наблюдений значение не суммируется и приоритет не назначается.","basis":reason+"; "+route_reason})
    observed_phrases = {norm(r["query"]) for r in active}
    for code in sorted(codes):
        if norm(code) not in observed_phrases:
            p = by_code[code]
            candidate.append({"query":code,"normalized_query":norm(code),"target_id":f"product:{p['id']}","target_url":f"/catalog/{p['id']}/","layer":"unmeasured_catalog_code","measurement_status":"unmeasured","reason":"Номер из текущего каталога; частотность для точной записи не проверена"})
    # Only generate a typed variant from the actual catalog product name, and
    # include its SKU to avoid inventing category/product equivalence.
    for p in products:
        typed = " ".join(x for x in (p.get("shortName") or p.get("name"), p.get("brand"), str(p["sku"])) if x)
        if norm(typed) not in observed_phrases:
            candidate.append({"query":typed,"normalized_query":norm(typed),"target_id":f"product:{p['id']}","target_url":f"/catalog/{p['id']}/","layer":"unmeasured_catalog_typed_product","measurement_status":"unmeasured","reason":"Вариант составлен только из названия, бренда и артикула конкретной позиции каталога; не является измеренной формулировкой."})
    # Queue one conservative measurement candidate for each brand/category pair
    # actually represented by sellable products. Never infer missing pairs or
    # treat these generated phrases as observed demand.
    category_terms = {"injectors":"форсунки", "nozzles":"распылители", "pumps":"насосы", "valves":"клапаны", "other":"топливные запчасти"}
    observed_roots = set(evidence_by_phrase)
    queued_roots = {r["normalized_query"] for r in candidate}
    brand_urls = {"Bosch":"bosch", "Delphi":"delphi", "Denso":"denso", "John Deere":"john-deere", "VDO / Vitesco (Aumovio)":"vdo"}
    for brand, category in sorted(brand_category_display, key=lambda pair: (pair[0].casefold(), pair[1])):
        phrase = f"{category_terms.get(category, category)} {brand}"
        key = norm(phrase)
        if key not in observed_roots and key not in queued_roots:
            brand_url=f"/brands/{brand_urls.get(brand, norm(brand).replace(' ', '-'))}/"
            candidate.append({"query":phrase,"normalized_query":key,"target_id":f"category:{category}","target_url":f"/category/{category}/","secondary_link":brand_url,"layer":"unmeasured_catalog_brand_category","measurement_status":"unmeasured","reason":"Кандидат составлен только для фактически представленной в каталоге пары бренд/категория; спрос не измерен, совместимость отдельной позиции не подразумевается."})
            queued_roots.add(key)
    # Manual review candidates are retained separately from the active core.
    candidate.extend({"query":r["query"],"normalized_query":r["normalized_query"],"target_id":"","target_url":"","layer":"manual_review","measurement_status":"observed_unclassified","reason":r["reason"],"evidence_ids":r["evidence_ids"]} for r in review)

    # Core groups use text identifiers; each code belongs to exactly one canonical product.
    core_products=[]
    evidence_ids_by_code=defaultdict(list)
    for r in observations:
        hit=catalog_code_hit(r.get("original_query",r.get("query","")),codes)
        if hit:
            evidence_ids_by_code[hit].append(r["observation_id"])
    for p in sorted(products,key=lambda x:x["id"]):
        code_records=[]
        for c in p.get("codes",[]):
            c=str(c)
            shorthand = bool(re.search(r"/[A-Za-z0-9]+$",c)) and len(c.rsplit("/",1)[-1]) < 4
            canonical = c.casefold() == str(p["id"]).casefold()
            code_records.append({"value":c,"kind":"supplier_shorthand" if shorthand else "catalog_sku" if canonical else "additional_code","review_flag":"verify_as_literal_code" if shorthand else "canonical_sku" if canonical else "additional_number_without_interchangeability_claim"})
        owned={str(c) for c in p.get("codes",[])}
        evidence_ids=[]
        for c in owned: evidence_ids.extend(evidence_ids_by_code.get(c,[]))
        core_products.append({"sku":str(p["sku"]),"name":p.get("name"),"short_name":p.get("shortName"),"brand":p.get("brand"),"category":p.get("category"),"canonical_target":f"/catalog/{p['id']}/","codes":code_records,"evidence_ids":sorted(evidence_ids)})
    groups=defaultdict(list)
    for p in products: groups[(p.get("brand"),p.get("category"))].append(p["id"])
    serp_summary=None if not serp else {"file":"seo/semantic-core/serp-research.json","sha256":digest(SERP_SOURCE),"fetched_date":serp.get("fetchedDate"),"source_engine":serp.get("sourceEngine"),"method_limits":serp.get("method",{}).get("limits",[]),"queries":[{"id":q.get("id"),"query":q.get("query"),"intent":q.get("intent"),"target":q.get("target"),"decision":q.get("decision"),"source_urls":q.get("sourceUrls",[])} for q in serp.get("queries",[])]}
    core={"schema_version":1,"source":{"file":"notes/2026-10-12-wordstat-research.json","sha256":digest(SOURCE),"collected_at":source.get("collected_at"),"provider":"Yandex Wordstat","disclaimer":"Данные отражают только сохранённый снимок; новые частотности не проверялись."},"serp_research":serp_summary,"curated_decisions":{"file":"seo/semantic-core/curated-decisions.json","sha256":digest(CURATED_SOURCE),"count":len(curated_list)} if curated else None,"products":core_products,"brand_category_groups":[{"brand":b,"category":c,"skus":sorted((p["sku"] for p in products if p.get("brand")==b and p.get("category")==c)),"target_url":f"/category/{c}/","secondary_brand_url":f"/brands/{brand_urls.get(b, norm(b).replace(' ', '-'))}/"} for (b,c),v in sorted(groups.items())],"articles":articles,"parent_observations":parents,"observations_included_in_observations_csv":len(observations),"accepted_keyword_count":len(active),"excluded_keyword_count":len({norm(x["query"]) for x in excluded}),"manual_review_keyword_count":len(review),"candidate_count":len(candidate),"excluded_count":len(excluded),"manual_review_count":len(review)}
    code_kinds=Counter(c["kind"] for p in core_products for c in p["codes"])
    raw_rows=sum(len(q.get("rows",[])) for q in source["queries"])
    parsed_rows=sum(r.get("parse_status")=="rightmost_grouped_count" for r in observations)
    decision_roots=len(evidence_by_phrase)
    excluded_unique_keywords=len({norm(x["query"]) for x in excluded})
    coverage={"generated_from":{"source":SOURCE.relative_to(ROOT).as_posix(),"sha256":digest(SOURCE),"products":PRODUCTS.relative_to(ROOT).as_posix(),"products_sha256":digest(PRODUCTS),"articles":ARTICLES.relative_to(ROOT).as_posix(),"articles_sha256":digest(ARTICLES),"seo_state":SEO_STATE.relative_to(ROOT).as_posix(),"seo_state_sha256":digest(SEO_STATE),"serp_research":SERP_SOURCE.relative_to(ROOT).as_posix() if serp else None,"serp_research_sha256":digest(SERP_SOURCE) if serp else None,"curated_decisions":CURATED_SOURCE.relative_to(ROOT).as_posix() if curated else None,"curated_decisions_sha256":digest(CURATED_SOURCE) if curated else None},"snapshot_date":source.get("collected_at"),"source_query_count":len(source["queries"]),"parent_observations":len(parents),"raw_rows":raw_rows,"unique_raw_row_strings":len({r for q in source["queries"] for r in q.get("rows",[])}),"observation_records":len(observations),"parsed_numeric_rows":parsed_rows,"unparsed_rows":raw_rows-parsed_rows,"unique_observed_query_roots":decision_roots,"accepted_observed_keywords":len(active),"excluded_observations":len(excluded),"excluded_unique_keywords":excluded_unique_keywords,"manual_review_keywords":len(review),"products":len(products),"unique_codes":len(codes),"code_record_kinds":dict(sorted(code_kinds.items())),"brand_category_groups":len(groups),"articles":len(articles),"keyword_priority_counts":dict(sorted(Counter(x["priority"] for x in active).items())),"generated_unmeasured_candidates":len(candidate)-len(review),"non_summing_rule":"Все значения остаются отдельными наблюдениями по observation_id; пересекающиеся измерения не суммируются и не сворачиваются выбором максимума.","quoted_rows_rule":"Строки под родительской quoted-проверкой сохраняются как legacy_row_broad_under_quoted_parent, а не как exact phrase metrics.","serp_is_not_volume":True,"no_new_frequency_measurements":True}
    outputs={
      "core.json":json_bytes(core),
      "coverage.json":json_bytes(coverage),
      "keywords.csv":csv_bytes(active,["keyword_id","query","normalized_query","intent","primary_target","target_url","target_status","secondary_link","measurement_status","observed_value","metric_type","period","evidence_count","evidence_ids","priority","priority_basis","curated_decision_id","basis"]),
      "observations.csv":csv_bytes(observations,["observation_id","query_id","parent_query","query","original_query","normalized_query","raw_row","row_index","value","parse_status","metric_type","parent_metric_type","period","region","devices","source","source_query_index","classification","reason","curated_decision_id"]),
      "excluded.csv":csv_bytes(excluded,["observation_id","query","normalized_query","value","period","reason","source_query_id"]),
      "page-map.csv":csv_bytes(page_map,["target_id","target_type","url","sku","owned_codes","brand","category","secondary_links","status"]),
      "measurement-queue.csv":csv_bytes(candidate,["query","normalized_query","target_id","target_url","secondary_link","layer","measurement_status","reason","evidence_ids"]),
    }
    return outputs, coverage, products, codes, active, candidate

def validate(outputs, coverage, products, codes, active, candidate):
    assert coverage["observation_records"] == coverage["raw_rows"] + coverage["parent_observations"], coverage
    assert len(products) == coverage["products"] and len(codes) == coverage["unique_codes"]
    assert {str(p["sku"]) for p in products} == {r["sku"] for r in json.loads(outputs["core.json"])["products"]}
    assert {"RE543262","RE571640","DZ100212","DZ100221","DZ100217","DZ100216"} <= codes
    assert all(r["primary_target"] and r["target_url"] and r["evidence_count"] > 0 for r in active)
    active_roots={r["normalized_query"] for r in active}
    excluded_rows=list(csv.DictReader(outputs["excluded.csv"].decode("utf-8").splitlines()))
    excluded_roots={r["normalized_query"] for r in excluded_rows}
    queue_rows=list(csv.DictReader(outputs["measurement-queue.csv"].decode("utf-8").splitlines()))
    review_roots={r["normalized_query"] for r in queue_rows if r["layer"]=="manual_review"}
    all_roots={r["normalized_query"] for r in csv.DictReader(outputs["observations.csv"].decode("utf-8").splitlines()) if r["normalized_query"] and r["parse_status"]!="unparsed_header_or_no_count"}
    assert not (active_roots & excluded_roots or active_roots & review_roots or excluded_roots & review_roots)
    assert active_roots | excluded_roots | review_roots == all_roots, (len(active_roots),len(excluded_roots),len(review_roots),len(all_roots),len(all_roots-(active_roots|excluded_roots|review_roots)))
    assert coverage["excluded_unique_keywords"]==len(excluded_roots)
    assert all((r["observed_value"] is not None) == (r["metric_type"] != "multiple_observations" and r["metric_type"] != "unmeasured") for r in active)
    core = json.loads(outputs["core.json"])
    map_rows=list(csv.DictReader(outputs["page-map.csv"].decode("utf-8").splitlines()))
    known_targets = {r["target_id"]: r for r in map_rows}
    assert len(known_targets) == len(map_rows)
    seo_state=json.loads(SEO_STATE.read_text(encoding="utf-8"))
    assert all(r["primary_target"] in known_targets and known_targets[r["primary_target"]]["url"] == r["target_url"] for r in active)
    assert all((r["target_status"]=="proposed" and r["secondary_link"] in seo_state) or (r["target_status"]=="existing" and r["target_url"] in seo_state) for r in active)
    assert all(isinstance(p["sku"], str) for p in core["products"])
    assert [a["slug"] for a in core["articles"]] == [a["slug"] for a in article_records()]
    assert len(core["articles"]) == coverage["articles"]
    assert core["articles"] and len(core["articles"]) >= 11
    bosch_page = next(r for r in map_rows if r["target_id"] == "category:injectors/bosch")
    assert bosch_page["url"] == "/category/injectors/bosch/" and len(bosch_page["sku"].split("|")) == 10
    bosch_keywords = [r for r in active if "bosch" in r["normalized_query"] or "бош" in r["normalized_query"]]
    assert all(r["primary_target"] != "category:injectors" for r in bosch_keywords if r["intent"] == "commercial" and ("форсун" in r["normalized_query"] or "инжектор" in r["normalized_query"]))
    obs_rows=list(csv.DictReader(outputs["observations.csv"].decode("utf-8").splitlines()))
    assert len({r["observation_id"] for r in obs_rows}) == coverage["observation_records"]
    assert all(r["sku"] in {p["sku"] for p in products} for r in map_rows if r["target_type"]=="existing_product")
    assert parsed_row('- row "0445020089 135"',codes)[:2] == ("0445020089",135)
    assert parsed_row('- row "тнвд bosch 10 469"',codes)[:2] == ("тнвд bosch",10469)
    assert parsed_row('- row "Заголовок без числа"',codes)[1] is None
    assert parsed_row('- row "model 123456789"',codes)[2] == "ambiguous_terminal_number"
    code_owners=defaultdict(set)
    for p in json.loads(outputs["core.json"])["products"]:
        for c in p["codes"]: code_owners[c["value"]].add(p["sku"])
    assert all(len(v)==1 for v in code_owners.values())
    assert not any(not r["target_url"] for r in candidate if r["layer"] != "manual_review")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    outputs,coverage,products,codes,active,candidate=build()
    validate(outputs,coverage,products,codes,active,candidate)
    OUT.mkdir(parents=True,exist_ok=True)
    if args.check:
        stale=[]
        for name,expected in outputs.items():
            path=OUT/name
            if not path.exists() or path.read_bytes()!=expected: stale.append(name)
        if stale:
            print("Generated files are stale or differ: "+", ".join(stale),file=sys.stderr)
            return 1
        print(f"OK: {coverage['observation_records']} observations, {len(active)} accepted observed keywords, {len(candidate)} queue rows, {len(products)} products, {len(codes)} codes")
        return 0
    for name,content in outputs.items(): (OUT/name).write_bytes(content)
    print(f"Wrote {len(outputs)} files: {coverage['observation_records']} observations; {len(active)} accepted keywords; {len(candidate)} measurement/review rows")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
