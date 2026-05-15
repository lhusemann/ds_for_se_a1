import subprocess
import pandas as pd
from pathlib import Path
import re

# ==========================================
# 1. Konfiguration
# ==========================================
CLUSTER_DIRS = {
    "ACDC": Path("Week1_cluster/ACDC"),
    "Limbo": Path("Week1_cluster/Limbo"),
    "WCA_UEM": Path("Week1_cluster/WCA/wca-uem-cluster"),
    "WCA_UEMNM": Path("Week1_cluster/WCA/wca-uemnm-cluster")
}

JARS = {
    "A2A": "arcade_core_A2a.jar",
    "CVG": "arcade_core_Cvg.jar"
}

OUTPUT_CSV = "evaluation_results_w1_k50.csv"
TARGET_K = 50

# Explizite Definition der zu vergleichenden Paare gem. Vorgabe
COMPARISONS = [
    ("Limbo", "WCA_UEM"),
    ("Limbo", "WCA_UEMNM"),
    ("WCA_UEM", "ACDC"),
    ("WCA_UEMNM", "ACDC"),
    ("Limbo", "ACDC")
]

# ==========================================
# 2. Hilfsfunktionen
# ==========================================
def get_target_file(alg_name, c_dir, target_k):
    """Sucht die spezifische RSF-Datei für k=50 oder den Fallback für ACDC."""
    if not c_dir.exists():
        return None
        
    files = list(c_dir.rglob("*.rsf"))
    
    if alg_name == "ACDC":
        return files[0] if files else None
    
    for f in files:
        numbers = re.findall(r'\d+', f.name)
        if str(target_k) in numbers:
            return f
            
    return None

def run_metric(jar_path, file1, file2, metric_name):
    """Führt das ARCADE-JAR aus und parst die Metrik über Regex."""
    cmd = ["java", "-jar", jar_path, str(file1), str(file2)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        output = result.stdout.strip()
        
        if metric_name == "A2A":
            match = re.search(r"(\d+\.?\d*)", output)
            return float(match.group(1)) if match else "PARSE_ERR"
            
        elif metric_name == "CVG":
            matches = re.findall(r"is (\d+\.?\d*)", output)
            if len(matches) == 2:
                return f"{matches[0]}|{matches[1]}"
            elif len(matches) == 1:
                return float(matches[0])
            else:
                return "PARSE_ERR"
                
    except subprocess.CalledProcessError as e:
        return f"ERR: {e.returncode}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"

# ==========================================
# 3. Hauptausführung
# ==========================================
def main():
    # 1. Indexierung der exakten RSF-Dateien für den Vergleich
    target_files = {}
    for alg, c_dir in CLUSTER_DIRS.items():
        f = get_target_file(alg, c_dir, TARGET_K)
        if f:
            target_files[alg] = f
        else:
            print(f"WARNUNG: Keine Datei für {alg} mit Ziel-k={TARGET_K} in {c_dir} gefunden.")

    results = []

    # 2. Ausführung der spezifischen Paare
    for alg1, alg2 in COMPARISONS:
        if alg1 not in target_files or alg2 not in target_files:
            print(f"Überspringe Vergleich {alg1} <-> {alg2} (Fehlende Datei).")
            continue
            
        file1 = target_files[alg1]
        file2 = target_files[alg2]
        
        print(f"Processing: {alg1} ({file1.name}) <-> {alg2} ({file2.name})")
        
        row = {
            "Alg_1": alg1,
            "File_1": file1.name,
            "Alg_2": alg2,
            "File_2": file2.name
        }
        
        # Iteration über A2A und CVG Metriken
        for metric_name, jar_file in JARS.items():
            val = run_metric(jar_file, file1, file2, metric_name)
            row[metric_name] = val
            
        results.append(row)

    # 3. Datenbereinigung und Export
    df = pd.DataFrame(results)
    
    if not df.empty and 'CVG' in df.columns:
        # Splittet den kombinierten String der Coverage-Richtung A->B und B->A
        df[['CVG_A->B', 'CVG_B->A']] = df['CVG'].astype(str).str.split('|', expand=True)
        df = df.drop(columns=['CVG'])
    
    df.to_csv(OUTPUT_CSV, index=False, sep=';', decimal=',')
    print(f"\nEvaluation abgeschlossen. Ergebnisse exportiert nach: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()