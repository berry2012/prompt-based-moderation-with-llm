#!/bin/bash

# Grafana Dashboard Import Script
# This script imports all moderation system dashboards into Grafana

set -e

# Configuration
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"
DASHBOARD_DIR="$(dirname "$0")/dashboards"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Grafana is accessible
check_grafana() {
    print_status "Checking Grafana accessibility..."
    if curl -s -f "${GRAFANA_URL}/api/health" > /dev/null; then
        print_success "Grafana is accessible"
        return 0
    else
        print_error "Grafana is not accessible at ${GRAFANA_URL}"
        return 1
    fi
}

# Function to import a dashboard
import_dashboard() {
    local dashboard_file="$1"
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    print_status "Importing dashboard: $dashboard_name"
    
    # Create the import payload
    local import_payload=$(jq -n --argjson dashboard "$(cat "$dashboard_file")" '{
        dashboard: $dashboard,
        overwrite: true,
        inputs: []
    }')
    
    # Import the dashboard
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
        -d "$import_payload" \
        "${GRAFANA_URL}/api/dashboards/db")
    
    # Check if import was successful
    if echo "$response" | jq -e '.status == "success"' > /dev/null; then
        local dashboard_url=$(echo "$response" | jq -r '.url')
        print_success "Dashboard imported successfully: ${GRAFANA_URL}${dashboard_url}"
    else
        local error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
        print_error "Failed to import dashboard $dashboard_name: $error_message"
        return 1
    fi
}

# Function to create datasource if it doesn't exist
create_prometheus_datasource() {
    print_status "Checking Prometheus datasource..."
    
    # Check if datasource exists
    local datasource_check=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
        "${GRAFANA_URL}/api/datasources/name/prometheus")
    
    if echo "$datasource_check" | jq -e '.id' > /dev/null; then
        print_success "Prometheus datasource already exists"
        return 0
    fi
    
    print_status "Creating Prometheus datasource..."
    
    # Create datasource
    local datasource_payload='{
        "name": "prometheus",
        "type": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": true,
        "basicAuth": false
    }'
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
        -d "$datasource_payload" \
        "${GRAFANA_URL}/api/datasources")
    
    if echo "$response" | jq -e '.id' > /dev/null; then
        print_success "Prometheus datasource created successfully"
    else
        local error_message=$(echo "$response" | jq -r '.message // "Unknown error"')
        print_error "Failed to create Prometheus datasource: $error_message"
        return 1
    fi
}

# Function to wait for Grafana to be ready
wait_for_grafana() {
    print_status "Waiting for Grafana to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if check_grafana; then
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting 5 seconds..."
        sleep 5
        ((attempt++))
    done
    
    print_error "Grafana did not become ready within the timeout period"
    return 1
}

# Main execution
main() {
    print_status "Starting Grafana dashboard import process..."
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Please install jq first."
        exit 1
    fi
    
    # Wait for Grafana to be ready
    if ! wait_for_grafana; then
        exit 1
    fi
    
    # Create Prometheus datasource
    if ! create_prometheus_datasource; then
        print_warning "Failed to create datasource, but continuing with dashboard import..."
    fi
    
    # Import all dashboards
    local success_count=0
    local total_count=0
    
    for dashboard_file in "$DASHBOARD_DIR"/*.json; do
        if [ -f "$dashboard_file" ]; then
            ((total_count++))
            if import_dashboard "$dashboard_file"; then
                ((success_count++))
            fi
        fi
    done
    
    # Summary
    print_status "Dashboard import completed"
    print_success "Successfully imported: $success_count/$total_count dashboards"
    
    if [ $success_count -eq $total_count ]; then
        print_success "All dashboards imported successfully!"
        print_status "Access your dashboards at: ${GRAFANA_URL}/dashboards"
        print_status "Login credentials: ${GRAFANA_USER}/${GRAFANA_PASS}"
    else
        print_warning "Some dashboards failed to import. Check the logs above for details."
        exit 1
    fi
}

# Run main function
main "$@"
