📢 Observability Enabled TTS Microservice 🎙️

A production-ready Text-to-Speech (TTS) Microservice built with FastAPI and Microsoft Edge TTS, enhanced with complete Observability features like:

✅ Structured Logging
✅ Request Trace IDs
✅ Prometheus Metrics (Latency, Error Rate, Throughput)
✅ Monitoring Dashboard JSON
✅ Health Checks
✅ Graceful Shutdown Handling

🚀 Features

Convert text into MP3 speech audio

Structured request logging with Trace ID

Prometheus metrics tracking

Latency, Error Rate, Throughput monitoring

Health check + graceful shutdown support

Simple monitoring dashboard JSON

📌 Endpoints
Method	Endpoint	Description
GET	/health	Service health check
POST	/tts	Generate speech audio
GET	/metrics	Prometheus metrics
GET	/dashboard	Monitoring summary

📊 Metrics Tracked

Request Count (Throughput)

Request Latency

Error Rate

Audio File Size

📂 Storage Output

Audio Files → storage/audio/

Request Logs → storage/logs/