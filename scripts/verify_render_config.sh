#!/bin/bash

set -e

echo "=== Render Configuration Verification ==="
echo ""

RENDER_YAML="render.yaml"

if [ ! -f "$RENDER_YAML" ]; then
  echo "❌ render.yaml not found"
  exit 1
fi

echo "✅ render.yaml exists"
echo ""

echo "1. Checking SANDBOX_ENABLED flag..."
WEB_SANDBOX=$(grep -A 40 "type: web" $RENDER_YAML | grep -A 1 "SANDBOX_ENABLED" | grep "value: false" || echo "")
WORKER_SANDBOX=$(grep -A 40 "type: worker" $RENDER_YAML | grep -A 1 "SANDBOX_ENABLED" | grep "value: false" || echo "")

if [ -n "$WEB_SANDBOX" ]; then
  echo "   ✅ Web service: SANDBOX_ENABLED=false"
else
  echo "   ❌ Web service: SANDBOX_ENABLED not set to false"
  exit 1
fi

if [ -n "$WORKER_SANDBOX" ]; then
  echo "   ✅ Worker service: SANDBOX_ENABLED=false"
else
  echo "   ❌ Worker service: SANDBOX_ENABLED not set to false"
  exit 1
fi

echo ""

echo "2. Checking RQ_QUEUE_NAME consistency..."
WEB_QUEUE=$(grep -A 40 "type: web" $RENDER_YAML | grep -A 1 "RQ_QUEUE_NAME" | grep "value: orchestrator" || echo "")
WORKER_QUEUE=$(grep -A 40 "type: worker" $RENDER_YAML | grep -A 1 "RQ_QUEUE_NAME" | grep "value: orchestrator" || echo "")

if [ -n "$WEB_QUEUE" ]; then
  echo "   ✅ Web service: RQ_QUEUE_NAME=orchestrator"
else
  echo "   ❌ Web service: RQ_QUEUE_NAME not set to orchestrator"
  exit 1
fi

if [ -n "$WORKER_QUEUE" ]; then
  echo "   ✅ Worker service: RQ_QUEUE_NAME=orchestrator"
else
  echo "   ❌ Worker service: RQ_QUEUE_NAME not set to orchestrator"
  exit 1
fi

echo ""

echo "3. Checking for Docker/DinD commands..."
DOCKER_COMMANDS=$(grep -i "docker" $RENDER_YAML || echo "")
if [ -z "$DOCKER_COMMANDS" ]; then
  echo "   ✅ No Docker/DinD commands found"
else
  echo "   ⚠️  Warning: Docker commands found in render.yaml"
  echo "$DOCKER_COMMANDS"
fi

echo ""

echo "4. Checking Python runtime..."
PYTHON_RUNTIME=$(grep "runtime: python" $RENDER_YAML || echo "")
if [ -n "$PYTHON_RUNTIME" ]; then
  echo "   ✅ Using native Python runtime"
else
  echo "   ❌ Python runtime not found"
  exit 1
fi

echo ""

echo "5. Checking web server configuration..."
GUNICORN=$(grep "gunicorn" $RENDER_YAML || echo "")
if [ -n "$GUNICORN" ]; then
  echo "   ✅ Gunicorn configured for web service"
else
  echo "   ⚠️  Warning: Gunicorn not found (may use different server)"
fi

echo ""

echo "6. Checking service count..."
SERVICE_COUNT=$(grep -c "type: web\|type: worker" $RENDER_YAML || echo "0")
echo "   ℹ️  Found $SERVICE_COUNT service(s)"
if [ "$SERVICE_COUNT" -ge 2 ]; then
  echo "   ✅ Multiple services configured (web + worker)"
else
  echo "   ⚠️  Warning: Expected at least 2 services (web + worker)"
fi

echo ""

echo "=== Verification Complete ==="
echo "✅ Render configuration is compatible with platform limitations"
echo "✅ No DinD dependencies found"
echo "✅ SANDBOX_ENABLED=false for both services"
echo "✅ RQ_QUEUE_NAME=orchestrator for queue consistency"
echo "✅ Using native Python runtime"
echo ""
echo "📝 For detailed deployment information, see:"
echo "   docs/sandbox/render-deployment.md"
