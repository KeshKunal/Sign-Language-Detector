# Architecture

```text
React / Vite frontend (localhost:5173)
  ├─ Browser camera preview and MediaPipe Holistic
  ├─ 30-frame feature buffer and prediction confirmation UX
  ├─ Confirmed-only localStorage history
  └─ REST request to local FastAPI
       └─ Keras model loaded on CPU (localhost:8000)
             └─ Original sld.model architecture and class mapping
```

## Boundaries

- The browser extracts features; Python owns model inference. There is one inference implementation.
- `GET /api/health` reports API, model file, labels, input dimensions, and confidence threshold.
- `POST /api/predict` accepts a finite numeric `(30, 1662)` sequence, validates its shape, and returns class scores and the top class. It returns HTTP 503 when a checkpoint is absent.
- The React client suppresses a class suggestion below the configured threshold. Patient confirmation is a separate action and the only route to persistent communication history.
- Video and landmark data remain transient in the browser. The service does not expose training, profile, or database endpoints.
- The browser landmark assets are served from the installed package under `/mediapipe/`; no paid or hosted inference service is required.

## Local operation

The Windows launcher starts Uvicorn on loopback port 8000 and Vite on loopback port 5173. Runtime output is kept under ignored `logs/`. A trained model is an explicit local artifact under ignored `models/`. Confirmed communications are browser-local and can be cleared by the user.
