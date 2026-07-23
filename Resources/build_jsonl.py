import csv, json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "raw_resource.csv")
DB_PATH = os.path.join(BASE, "resource_database.jsonl")


MONTHS = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}


def normalize_date(raw):
    raw = raw.strip().strip('"')
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", raw)
    if m:
        mm = MONTHS.get(m.group(1).lower())
        if mm:
            return f"{int(m.group(2)):02d}-{mm}-{m.group(3)}"
    return raw


def structure_content(title, body):
    text = body.strip()
    text = re.sub(r"[ \t]{2,}", "  ", text)

    re_heading = re.compile(r"###\s*([A-Za-z][A-Za-z &'/()\-]+)\s*:?\s*")
    re_num = re.compile(r"\s*(\d+)[\.\)]\s+([A-Z][\w &'/()\-]*?)\s*:\s*")
    re_num_bare = re.compile(r"\s*(\d+)[\.\)]\s+")
    re_bullet = re.compile(r"\s*[\*\-]\s+([A-Z][\w &'/()\-]*?)\s*:\s*")
    re_bullet_bare = re.compile(r"\s*[\*\-]\s+")
    re_prompt_label = re.compile(r'["\s]*(text|markdown|prompt)["\s]*:\s*', re.I)

    segments = []
    pos = 0
    n = len(text)
    while pos < n:
        m = re_heading.match(text, pos)
        if m:
            segments.append(("h", m.group(1).strip()))
            pos = m.end()
            continue
        m = re_num.match(text, pos)
        if m:
            label = m.group(2).strip()
            rest = text[m.end():]
            end = len(rest)
            best = None
            for pat in (re_num, re_num_bare, re_bullet, re_bullet_bare, re_prompt_label, re_heading):
                mm = pat.search(rest)
                if mm and (best is None or mm.start() < best):
                    best = mm.start()
            if best is not None:
                end = best
            b = re.sub(r"\s+", " ", rest[:end].strip()).strip().strip(" :")
            if b:
                segments.append(("num", m.group(1), f"**{label}:** {b}"))
            else:
                segments.append(("num", m.group(1), f"**{label}**"))
            pos = m.end() + end
            continue
        m = re_num_bare.match(text, pos)
        if m:
            rest = text[m.end():]
            end = len(rest)
            best = None
            for pat in (re_num, re_num_bare, re_bullet, re_bullet_bare, re_prompt_label, re_heading):
                mm = pat.search(rest)
                if mm and (best is None or mm.start() < best):
                    best = mm.start()
            if best is not None:
                end = best
            b = re.sub(r"\s+", " ", rest[:end].strip()).strip().strip(" :")
            if b:
                segments.append(("num", m.group(1), b))
            pos = m.end() + end
            continue
        m = re_bullet.match(text, pos)
        if m:
            label = m.group(1).strip()
            rest = text[m.end():]
            end = len(rest)
            for pat in (re_heading, re_num, re_num_bare, re_bullet, re_bullet_bare):
                mm = pat.search(rest)
                if mm:
                    end = mm.start()
            b = re.sub(r"\s+", " ", rest[:end].strip()).strip().strip(" :")
            if b:
                segments.append(("bul", f"**{label}:** {b}"))
            else:
                segments.append(("bul", f"**{label}**"))
            pos = m.end() + end
            continue
        m = re_bullet_bare.match(text, pos)
        if m:
            rest = text[m.end():]
            end = len(rest)
            best = None
            for pat in (re_heading, re_num, re_num_bare, re_bullet, re_bullet_bare):
                mm = pat.search(rest)
                if mm and (best is None or mm.start() < best):
                    best = mm.start()
            if best is not None:
                end = best
            b = re.sub(r"\s+", " ", rest[:end].strip()).strip().strip(" :")
            if b:
                segments.append(("bul", b))
            pos = m.end() + end
            continue
        m = re_prompt_label.match(text, pos)
        if m and (pos == 0 or text[pos - 1] in (" ", '"')):
            rest = text[pos + len(m.group(0)):]
            end = len(rest)
            for pat in (re_heading, re_num, re_num_bare, re_bullet, re_bullet_bare):
                mm = pat.search(rest)
                if mm:
                    end = mm.start()
            prompt = re.sub(r"\s+", " ", rest[:end].strip()).strip()
            prompt = re.sub(r'^prompt\s*:\s*', '', prompt, flags=re.I)
            if prompt:
                segments.append(("code", prompt))
            pos = pos + len(m.group(0)) + end
            continue
        chunk = text[pos:]
        end = len(chunk)
        for pat in (re_heading, re_num, re_num_bare, re_bullet, re_bullet_bare, re_prompt_label):
            mm = pat.search(chunk)
            if mm and mm.start() > 0:
                end = mm.start()
                break
        seg = re.sub(r"\s+", " ", chunk[:end].strip()).strip().strip(" :")
        if seg:
            segments.append(("p", seg))
        pos = pos + end
        if end == 0:
            pos += 1
    return segments


def render(title, segments):
    out = [f"## {title}"]
    for seg in segments:
        t = seg[0]
        if t == "h":
            out.append(f"### {seg[1]}")
        elif t == "num":
            out.append(f"{seg[1]}. {seg[2]}")
        elif t == "bul":
            out.append(f"- {seg[1]}")
        elif t == "code":
            out.append("```")
            out.append(seg[1])
            out.append("```")
        elif t == "p":
            out.append(seg[1])
    return "\n\n".join(out)


def split_title_body(text):
    text = text.strip()
    intro = ""
    m = re.search(r"###", text)
    if not (m and m.start() > 4):
        m = re.search(r"(\d+[\.\)]\s+[A-Z][\w &'/()\-]*?:|\*\s+[A-Z][\w &'/()\-]*?:|\-\s+[A-Z][\w &'/()\-]*?:|\btext\s*:|\bmarkdown\s*:|\bprompt\s*:)", text)
    if m and m.start() > 4:
        head = text[:m.start()].strip()
        body = text[m.start():].strip()
        sm = re.split(r"(?<=[.!?])\s+", head, maxsplit=1)
        if len(sm) > 1:
            title = sm[0].strip()
            intro = sm[1].strip()
        else:
            sm2 = re.split(r"\s{2,}", head, maxsplit=1)
            title = sm2[0].strip()
            intro = sm2[1].strip() if len(sm2) > 1 else ""
        if intro:
            body = intro + "\n\n" + body
    else:
        sm2 = re.split(r"\s{2,}", text, maxsplit=1)
        if len(sm2) > 1:
            title = sm2[0].strip()
            body = sm2[1].strip()
        else:
            parts = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)
            title = parts[0].strip()
            body = parts[1].strip() if len(parts) > 1 else ""
    title = re.sub(r"\s*:\s*$", "", title).strip()
    return title, body


def build_entry(row, new_sno):
    raw = row["Extracted Content (Markdown)"].strip()
    title, body = split_title_body(raw)
    if not body:
        structured = f"## {title}"
    else:
        segments = structure_content(title, body)
        structured = render(title, segments)
    return {
        "s_no": str(new_sno),
        "source_newsletter": row["Source Newsletter"].strip(),
        "date_of_appearance": normalize_date(row["Date of Appearance"]),
        "content_type": row["Content Type"].strip(),
        "theme": row["Theme"].strip(),
        "extracted_content": structured,
        "sponsored_content": row["Sponsored Content"].strip(),
        "target_persona": row["Target Persona"].strip(),
        "estimated_setup_time": row["Estimated Setup Time"].strip(),
    }


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Determine starting s_no so we never collide with the existing database.
    existing = []
    if os.path.exists(DB_PATH):
        with open(DB_PATH, encoding="utf-8") as f:
            existing = [json.loads(l) for l in f if l.strip()]
    start = 1
    if existing:
        nums = [int(e.get("s_no", 0)) for e in existing if str(e.get("s_no", "")).isdigit()]
        start = (max(nums) + 1) if nums else 1

    new_entries = [build_entry(r, start + i) for i, r in enumerate(rows)]

    # Idempotency guard: if the CSV content was already appended (detected by
    # matching the last entries' structured content), do not append again.
    existing_contents = {e.get("extracted_content", "") for e in existing}
    if new_entries and new_entries[0]["extracted_content"] in existing_contents:
        print("ABORT: these CSV entries already appear to be in the database. "
              "No changes made.")
        return

    with open(DB_PATH, "a", encoding="utf-8") as f:
        for e in new_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Appended {len(new_entries)} entries (s_no {start}..{start + len(new_entries) - 1})")


if __name__ == "__main__":
    main()
