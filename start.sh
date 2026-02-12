#!/bin/bash
# Ecom-Watch — Launch Script
# Starts both the FastAPI backend and Vite React frontend

echo "================================================"
echo "  Ecom-Watch — Laptop Promotion Intelligence"
echo "================================================"
echo ""

# [FIX] Use the actual WORK_DIR path for DB check, not relative path
WORK_DIR="/sessions/practical-youthful-faraday/ecom-watch-work"
DB_PATH="$WORK_DIR/data/ecom-watch.db"

if [ ! -f "$DB_PATH" ]; then
  echo ">> First run: importing historical data from Excel..."
  cd backend && python database/seed.py && cd ..
  echo ""
fi

# [FIX] Bind to 127.0.0.1 instead of 0.0.0.0 to match CORS policy
echo ">> Starting backend API (port 8000)..."
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend dev server
echo ">> Starting frontend (port 5173)..."
cd frontend
npx vite --host 127.0.0.1 --port 5173 &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================================"
echo "  Dashboard: http://localhost:5173"
echo "  API:       http://localhost:8000/api/health"
echo "================================================"
echo ""
echo "Press Ctrl+C to stop both servers"

# Trap Ctrl+C to kill both
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
