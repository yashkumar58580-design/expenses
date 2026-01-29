FROM python:3.9

WORKDIR /app

# Pehle requirements install karte hain
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Phir baaki saara code copy karte hain
COPY . .

# Port expose karna zaroori hai
EXPOSE 8000

# Server start karne ki command
CMD ["uvicorn", "Adv_api_inr:app", "--host", "0.0.0.0", "--port", "8000"]
