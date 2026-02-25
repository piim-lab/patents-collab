import csv
import json
import glob
import os

JSON_PATH = "../data/final/*.json"
HOLDERS_CSV = "./PatentHolders.csv"
OUTPUT_CSV = "./participants.csv"

GRANTED_CODES = {"16.1", "16.3"}
IPC_LETTERS = list("ABCDEFGH")

def load_holders(csv_path):
    holders = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            holder_id = int(row["holder_id"])

            holders[holder_id] = {
                "holder_id": row["holder_id"],
                "nome": row["fullName"],
                "tipo": row["type"],
                "depositadas": 0,
                "concedidas": 0,
                **{f"{c}_depositadas": 0 for c in IPC_LETTERS},
                **{f"{c}_concedidas": 0 for c in IPC_LETTERS},
            }

    return holders

def process_patents(holders):
    json_files = glob.glob(JSON_PATH)
    total = len(json_files)

    print(f"Processando {total} patentes...")

    for i, path in enumerate(json_files, start=1):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        if "title" not in data:
            continue

        granted = 0
        for event in data.get("events", []):
            if event.get("code") in GRANTED_CODES:
                granted = 1
                break

        ipc_letters = set()

        for code in data.get("ipcCodes", []):
            if code:
                letter = code[0].upper()
                if letter in IPC_LETTERS:
                    ipc_letters.add(letter)

        for holder_id in data.get("holders", []):
            holder = holders.get(holder_id)
            if not holder:
                continue

            holder["depositadas"] += 1
            holder["concedidas"] += granted

            for letter in ipc_letters:
                holder[f"{letter}_depositadas"] += 1
                if granted:
                    holder[f"{letter}_concedidas"] += 1

        if i % 2000 == 0 or i == total:
            pct = (i / total) * 100
            print(f"{i}/{total} — {pct:.2f}%")

def write_output_csv(holders, output_path):
    fieldnames = ["holder_id", "nome", "tipo", "depositadas", "concedidas"]

    for c in IPC_LETTERS:
        fieldnames.append(f"{c}_depositadas")
        fieldnames.append(f"{c}_concedidas")

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for holder in holders.values():
            writer.writerow(holder)

def main():
    print("Carregando holders")
    holders = load_holders(HOLDERS_CSV)

    process_patents(holders)

    print("Gerando CSV final")
    write_output_csv(holders, OUTPUT_CSV)

    print("Concluído")

if __name__ == "__main__":
    main()
