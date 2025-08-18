# Test forcé immédiat pour générer des données visibles dans Azure

echo "=== TEST FORCÉ POUR AZURE INSIGHTS ==="
echo "Génération de données immédiates..."

# Test massif pour être sûr que les données arrivent
echo "1. Envoi de 10 prédictions distinctes..."
for i in {1..10}; do
  timestamp=$(date +%s)
  curl -s -X POST "http://localhost:8000/predict" \
    -H "Content-Type: application/json" \
    -d "{
      \"text\": \"Test Azure massif $i - timestamp $timestamp - excellent service Air Paradis!\",
      \"user_id\": \"mass_test_user_$i\"
    }" > /dev/null
  echo "   Prédiction $i envoyée"
done

echo ""
echo "2. Envoi de 10 feedbacks distincts..."
for i in {1..10}; do
  timestamp=$(date +%s)
  curl -s -X POST "http://localhost:8000/feedback" \
    -H "Content-Type: application/json" \
    -d "{
      \"feedback_type\": \"correct\",
      \"prediction_id\": \"mass_test_$i\", 
      \"original_sentiment\": \"positive\",
      \"original_confidence\": 0.9$i,
      \"user_id\": \"mass_test_user_$i\"
    }" > /dev/null
  echo "   Feedback $i envoyé"
done

echo ""
echo "3. Vérification des compteurs Azure..."
counters=$(curl -s "http://localhost:8000/debug/azure-status" | jq '.service_status | {predictions_count, feedback_count, logs_sent, logs_failed}')
echo "$counters"

echo ""
echo "4. Forcer un test direct Azure..."
curl -s -X POST "http://localhost:8000/debug/test-azure" > /dev/null 2>&1
echo "   Test Azure direct envoyé"

echo ""
echo "=== MAINTENANT DANS AZURE PORTAL ==="
echo "1. Cliquez sur 'Événements' dans le menu de gauche"
echo "2. OU cherchez 'Logs' ou 'Journaux'"
echo "3. Dans l'éditeur de requêtes, collez ceci:"
echo ""
echo "customEvents"
echo "| where timestamp > ago(1h)"
echo "| extend eventType = tostring(customDimensions.event_type)"
echo "| extend userId = tostring(customDimensions.user_id)"
echo "| project timestamp, name, eventType, userId"
echo "| order by timestamp desc"
echo ""
echo "4. Cliquez 'Exécuter' (Run)"
echo ""
echo "VOUS DEVRIEZ VOIR:"
echo "- 20+ événements"
echo "- event_type: 'prediction' et 'user_feedback'"
echo "- user_id: 'mass_test_user_1', 'mass_test_user_2', etc."

echo ""
echo "⏰ IMPORTANT: Si pas de résultats, attendez 5 minutes et réessayez"
echo "Les données Azure peuvent prendre du temps à apparaître"

echo ""
echo "=== DEBUGGING SI TOUJOURS RIEN ==="
echo "Si toujours 0 résultats après 10 minutes:"
echo "1. Vérifiez la période: changez 'ago(1h)' en 'ago(24h)'"
echo "2. Essayez cette requête plus large:"
echo ""
echo "union traces, customEvents, requests, dependencies"
echo "| where timestamp > ago(24h)"
echo "| order by timestamp desc"