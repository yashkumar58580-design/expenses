# Python ka image use karein
FROM python:3.9

# Folder set karein
WORKDIR /app

# Sabse pehle requirements copy aur install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karein
COPY . .

# FastAPI ko run karne ki command
CMD ["uvicorn", "Adv_api_inr:app", "--host", "0.0.0.0", "--port", "8000"]