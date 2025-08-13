# Script de test pour valider la logique et consistance du modèle
import requests
import json

API_BASE_URL = "http://localhost:8000"

# Cas de test avec résultats attendus pour validation du modèle
test_cases = [
    {
        "text": "Service excellent d'Air Paradis, je recommande vivement!",
        "expected": "positive",
        "description": "Texte clairement positif"
    },
    {
        "text": "Vol retardé de 5 heures, personnel désagréable, pire expérience!",
        "expected": "negative", 
        "description": "Texte clairement négatif"
    },
    {
        "text": "Vol Paris-Londres, départ 15h30, arrivée prévue 16h45.",
        "expected": "neutral",
        "description": "Texte neutre/informatif"
    },
    {
        "text": "le vol était en retard, mais j'ai fais de belles rencontres",
        "expected": "positive",
        "description": "Texte mixte avec aspect positif dominant"
    },
    {
        "text": "Parfait! Équipage formidable et vol à l'heure",
        "expected": "positive",
        "description": "Très positif avec superlatifs"
    },
    {
        "text": "Catastrophe totale, jamais plus avec cette compagnie",
        "expected": "negative",
        "description": "Très négatif avec mots forts"
    },
    {
        "text": "I love this airline! Great service and comfortable seats.",
        "expected": "positive",
        "description": "Très positif avec mots forts"
    },    
    {
        "text": "Worst flight ever! Delayed for 3 hours and no explanation.",
        "expected": "negative",
        "description": "Très négatif avec mots forts"
    },
    {
        "text": "The food was decent, staff was helpful overall.",
        "expected": "positive",
        "description": "Globalement positif"
    },
    {
        "text": "Amazing crew! They were so helpful and friendly.",
        "expected": "positive",
        "description": "Très positif"
    },
    {
        "text": "Terrible experience. Lost my luggage and rude staff.",
        "expected": "negative",
        "description": "Très négatif"
    },
    {
        "text": "Flight was on time and smooth. Good job!",
        "expected": "positive",
        "description": "Positif avec compliment"
    },
    {
        "text": "Disappointed with the service. Will not fly again.",
        "expected": "negative",
        "description": "Négatif avec intention claire"
    },
    {
        "text": "Great value for money. Recommended!",
        "expected": "positive",
        "description": "Positif avec recommandation"
    },
    {
        "text": "The plane was dirty and the seats uncomfortable.",
        "expected": "negative",
        "description": "Négatif sur conditions"
    },
    {
        "text": "Excellent customer service. Thank you!",
        "expected": "positive",
        "description": "Très positif avec remerciement"
    },
    {
        "text": "Not the worst but could be better.",
        "expected": "negative",
        "description": "Critique modérée"
    },
    {
        "text": "Satisfactory service, met my expectations.",
        "expected": "positive",
        "description": "Satisfaction exprimée"
    },
    {
        "text": "Outstanding experience from start to finish!",
        "expected": "positive",
        "description": "Très positif avec enthousiasme"
    },
    {
        "text": "Complete disaster, never again!",
        "expected": "negative",
        "description": "Très négatif catégorique"
    },
    {
        "text": "Good enough for the price I paid.",
        "expected": "positive",
        "description": "Positif modéré"
    }  
]

def test_model_logic():
    """Test de la logique de prédiction du modèle sur des cas types"""
    print("Test de la logique du modèle")
    print("=" * 60)
    
    correct_predictions = 0
    total_tests = len(test_cases)
    inconsistent_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Texte: '{test_case['text']}'")
        
        try:
            # Appel API pour prédiction
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json={"text": test_case['text'], "user_id": f"test_{i}"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                predicted = result['sentiment']
                confidence = result['confidence']
                model_info = result.get('model_info', {})
                
                print(f"Prédit: {predicted} (confiance: {confidence:.3f})")
                print(f"Attendu: {test_case['expected']}")
                print(f"Modèle: {model_info.get('name', 'unknown')} ({model_info.get('source', 'unknown')})")
                
                # Vérification de la prédiction
                if predicted == test_case['expected']:
                    print("[✓] Prédiction correcte")
                    correct_predictions += 1
                else:
                    print("[X] Prédiction incorrecte")
                    inconsistent_results.append({
                        'text': test_case['text'],
                        'expected': test_case['expected'],
                        'predicted': predicted,
                        'confidence': confidence
                    })
                    
            else:
                print(f"[X] Erreur API: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"[X] Exception: {e}")
    
    # Calcul et affichage des résultats
    accuracy = correct_predictions / total_tests * 100
    print(f"\nRésultats finaux:")
    print(f"Accuracy sur cas de test: {accuracy:.1f}% ({correct_predictions}/{total_tests})")
    
    if inconsistent_results:
        print(f"\nPrédictions incorrectes:")
        for result in inconsistent_results:
            print(f"  '{result['text'][:50]}...' → {result['predicted']} (attendu: {result['expected']})")
    
    # Évaluation globale
    if accuracy >= 75:
        print("[✓] Modèle fonctionne correctement")
    elif accuracy >= 50:
        print("[!] Modèle partiellement fonctionnel")
    else:
        print("[X] Modèle défaillant - corrections nécessaires")
    
    return accuracy, inconsistent_results

def test_consistency():
    """Test de consistance - vérifier que les mêmes textes donnent les mêmes résultats"""
    print("\nTest de consistance")
    print("=" * 40)
    
    # Textes de test pour vérifier la consistance
    test_texts = [
        "Service parfait, je recommande!",
        "Vol horrible, personnel désagréable",
        "le vol était en retard, mais j'ai fais de belles rencontres"
    ]
    
    all_consistent = True
    
    for text in test_texts:
        print(f"\nTest consistance: '{text[:40]}...'")
        
        results = []
        # Tester 3 fois le même texte
        for i in range(3):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/predict",
                    json={"text": text, "user_id": f"consistency_{i}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    results.append((result['sentiment'], round(result['confidence'], 4)))
                
            except Exception as e:
                print(f"Erreur essai {i+1}: {e}")
        
        # Vérification de la consistance
        if results:
            unique_results = set(results)
            if len(unique_results) == 1:
                print(f"[✓] Consistant: {results[0][0]} (confiance: {results[0][1]})")
            else:
                print("[X] Inconsistant:")
                for result in unique_results:
                    print(f"   {result[0]} (confiance: {result[1]})")
                all_consistent = False
    
    if all_consistent:
        print("\n[✓] Toutes les prédictions sont consistantes")
    else:
        print("\n[X] Prédictions inconsistantes détectées")
        print("   → Problème probable: vectorisation aléatoire")
    
    return all_consistent

def test_api_health():
    """Test de santé de l'API"""
    print("\nTest de santé de l'API")
    print("=" * 35)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"Status: {health['status']}")
            print(f"Modèle chargé: {health['model_loaded']}")
            print(f"Message: {health['message']}")
            
            if health.get('model_info'):
                model_info = health['model_info']
                print(f"Info modèle: {model_info}")
            
            return health['model_loaded']
        else:
            print(f"[X] API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[X] Erreur health check: {e}")
        return False

def main():
    """Fonction principale - lance tous les tests de validation"""
    print("Validation complète du modèle")
    print("=" * 70)
    
    # Test de santé de l'API
    is_healthy = test_api_health()
    
    if not is_healthy:
        print("\n[X] API non opérationnelle - arrêt des tests")
        return
    
    # Test de consistance des prédictions
    is_consistent = test_consistency()
    
    # Test de logique métier
    accuracy, errors = test_model_logic()
    
    # Résumé final et recommandations
    print("\n" + "=" * 70)
    print("Résumé final")
    print("=" * 70)
    
    if is_consistent and accuracy >= 75:
        print("Modèle validé - Prêt pour la production")
        print(f"   [✓] Consistance: OK")
        print(f"   [✓] Accuracy: {accuracy:.1f}%")
    elif is_consistent:
        print("Modèle partiellement fonctionnel")
        print(f"   [✓] Consistance: OK")
        print(f"   [!] Accuracy: {accuracy:.1f}% (perfectible)")
    else:
        print("Modèle défaillant")
        print(f"   [X] Consistance: KO")
        print(f"   [X] Accuracy: {accuracy:.1f}%")
        print("\nActions requises:")
        print("   1. Vérifier le chargement du tokenizer")
        print("   2. Corriger la vectorisation")
        print("   3. Re-tester après corrections")

if __name__ == "__main__":
    main()