FROM agent-engine-platform-backend:latest

WORKDIR /app

# Copy updated application code
COPY . .

# Ensure uploads dir exists
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
