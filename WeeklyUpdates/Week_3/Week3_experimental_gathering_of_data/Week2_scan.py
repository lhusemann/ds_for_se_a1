import subprocess
import pandas as pd
from pathlib import Path
import re

# 1. Konfiguration
ARC_DIR = Path("colab_output")
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

OUTPUT_CSV = "evaluation_results.csv"

def is_valid_pair(arc_name, cluster_name, alg_name):
    if alg_name == "ACDC":
        return True

    # Extrahiere k aus ARC-File (Voraussetzung: Prefix _c)
    arc_match = re.search(r'_c(\d+)', arc_name, re.IGNORECASE)
    if not arc_match:
        return False
        
    arc_k = arc_match.group(1)
    
    # Extrahiere alle numerischen Substrings aus dem Cluster-Namen
    cluster_numbers = re.findall(r'\d+', cluster_name)
    
    # Validierung: Entspricht arc_k einem der k-Parameter im Cluster-Namen?
    return arc_k in cluster_numbers

def run_metric(jar_path, file1, file2, metric_name):
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

def main():
    # rglob für rekursive Suche im ARC-Verzeichnis (falls nötig)
    arc_files = list(ARC_DIR.rglob("*.rsf"))
    results = []

    for arc_file in arc_files:
        for alg_name, c_dir in CLUSTER_DIRS.items():
            # rglob fixt potenzielle Sub-Directory Misses der Cluster-Algorithmen
            cluster_files = list(c_dir.rglob("*.rsf"))
            
            for c_file in cluster_files:
                if not is_valid_pair(arc_file.name, c_file.name, alg_name):
                    continue
                    
                print(f"Processing: {arc_file.name} <-> {c_file.name} ({alg_name})")
                
                row = {
                    "ARC_File": arc_file.name,
                    "Cluster_Alg": alg_name,
                    "Cluster_File": c_file.name
                }
                
                for metric_name, jar_file in JARS.items():
                    val = run_metric(jar_file, arc_file, c_file, metric_name)
                    row[metric_name] = val
                    
                results.append(row)

    df = pd.DataFrame(results)
    
    if 'CVG' in df.columns:
        df[['CVG_A->B', 'CVG_B->A']] = df['CVG'].str.split('|', expand=True)
        df = df.drop(columns=['CVG'])
    
    df.to_csv(OUTPUT_CSV, index=False, sep=';', decimal=',')
    print(f"\nEvaluation abgeschlossen. Ergebnisse gespeichert in: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()