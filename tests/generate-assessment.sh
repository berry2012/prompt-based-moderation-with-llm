#!/bin/bash

echo "Generating test data for Grafana dashboards..."

# Array of test messages
declare -a normal_messages=(
    "Hello everyone, how are you doing today?"
    "Great weather we're having!"
    "Thanks for the help with the project"
    "Looking forward to the meeting tomorrow"
    "Have a wonderful day!"
)

declare -a toxic_messages=(
    "You are the worst human being, you make me sick to my stomach."
    "I hate you so much, you're absolutely terrible"
    "You're such an idiot, I can't stand you"
    "Go away, nobody wants you here"
    "You're completely useless and worthless"
)

# Send normal messages
echo "Sending normal messages..."
for i in {1..5}; do
    message=${normal_messages[$((i-1))]}
    curl -s -X POST "http://localhost:8002/api/send-message" \
      -H "Content-Type: application/json" \
      -d "{
        \"message\": \"$message\",
        \"user_id\": \"normal_user_$i\",
        \"username\": \"NormalUser$i\",
        \"channel_id\": \"general\"
      }" > /dev/null
    echo "Sent normal message $i"
    sleep 2
done

# Send toxic messages
echo "Sending toxic messages..."
for i in {1..5}; do
    message=${toxic_messages[$((i-1))]}
    curl -s -X POST "http://localhost:8002/api/send-message" \
      -H "Content-Type: application/json" \
      -d "{
        \"message\": \"$message\",
        \"user_id\": \"toxic_user_$i\",
        \"username\": \"ToxicUser$i\",
        \"channel_id\": \"general\"
      }" > /dev/null
    echo "Sent toxic message $i"
    sleep 2
done

echo "Test data generation completed!"
echo "Check your Grafana dashboards at http://localhost:3000"