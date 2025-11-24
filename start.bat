@echo off
echo Starting Portfolio Manager...

:: Start Backend
start "Portfolio Manager Backend" cmd /k "cd backend && uvicorn main:app --reload"
:: If venv doesn't exist, try global python (assuming dependencies installed)
:: fallback: start "Portfolio Manager Backend" cmd /k "cd backend && uvicorn main:app --reload"

:: Start Frontend
start "Portfolio Manager Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend running at http://localhost:8000
echo Frontend running at http://localhost:3001
echo.
echo API Docs available at http://localhost:8000/docs
echo.
pause
