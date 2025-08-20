# script pour automatiser les tests dans un pipeline CI/CD
import subprocess
import sys
import json
from datetime import datetime

def run_unit_tests():
    """Exécute les tests unitaires et retourne les résultats"""
    print("=== EXECUTION DES TESTS UNITAIRES ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Exécution de pytest avec sortie JSON
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_api.py", 
            "--json-report", 
            "--json-report-file=test_results.json",
            "-v"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Code de retour: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Lecture des résultats JSON si disponible
        try:
            with open("test_results.json", "r") as f:
                test_data = json.load(f)
                print(f"\\nRésumé des tests:")
                print(f"- Tests exécutés: {test_data.get('summary', {}).get('total', 0)}")
                print(f"- Réussis: {test_data.get('summary', {}).get('passed', 0)}")
                print(f"- Échecs: {test_data.get('summary', {}).get('failed', 0)}")
        except:
            print("Impossible de lire les résultats JSON")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("ERREUR: Timeout des tests (>60s)")
        return False
    except Exception as e:
        print(f"ERREUR lors de l'exécution des tests: {e}")
        return False

if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)