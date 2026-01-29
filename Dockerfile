# Python aur Node dono ka combo
FROM nikolaik/python-nodejs:python3.9-nodejs18

WORKDIR /app
COPY . .

# Backend dependencies
RUN pip install -r requirements.txt

# Frontend build (Agar React hai)
RUN npm install && npm run build

# Server start karne ki command
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "80"]