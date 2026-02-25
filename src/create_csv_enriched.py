import csv
import json
import glob
from collections import defaultdict


HOLDER_CSV = "PatentHolders.csv"
INPUT_CSV = "participants.csv"
OUTPUT_CSV = "participants_enriched.csv"
JSON_PATH = "../data/final/*.json"

holder_country = {}

with open(HOLDER_CSV, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        holder_id = int(row["holder_id"])
        holder_country[holder_id] = row.get("country", "").strip()

print(f"Holders carregados: {len(holder_country)}")


collaborators = defaultdict(set)

json_files = glob.glob(JSON_PATH)
total = len(json_files)

for i, path in enumerate(json_files, 1):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        continue

    if "holders" not in data or not data["holders"]:
        continue

    holders = list(set(data["holders"]))

    if len(holders) < 2:
        continue

    for h in holders:
        for other in holders:
            if h != other:
                collaborators[h].add(other)

    if i % 10000 == 0:
        print(f"{i}/{total} JSONs processados")

print("Colaborações calculadas.")


with open(INPUT_CSV, encoding="utf-8") as infile, \
    open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as outfile:

    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ["num_colaboradores", "is_foreign"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)

    writer.writeheader()

    for row in reader:
        holder_name = row["nome"]

        holder_id = int(row["holder_id"])
        row["num_colaboradores"] = len(collaborators.get(holder_id, set()))
        row["is_foreign"] = 1 if holder_country.get(holder_id) != "BR" else 0

        writer.writerow(row)

print(f"CSV enriquecido salvo em: {OUTPUT_CSV}")
