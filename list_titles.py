import json

for i in range(1, 21):
    data = json.load(open(f"raw_chapters/v1c{i}.json", encoding="utf-8"))
    title_para = data["paragraphs"][0] if data["paragraphs"] else "No Title"
    print(f"Ch {i:02d}: {title_para}")
