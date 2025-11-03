# 🗺️ Location History API

A simple Flask-based API that tracks historical places and location history using SQLAlchemy and Tavily Search integration.

---

## 🚀 Features

* Fetch location history with timestamps and descriptions
* Retrieve historical places for a given location
* Integrated with **Tavily Search** for smart information retrieval
* Lightweight and easy to deploy on **RunPod** or **any Flask environment**

---

## 📦 Project Structure

```
├── app.py              # Main Flask app and routes
├── writer.py           # Handles logic for Tavily integration
├── utils.py            # Helper functions (Tavily search wrapper)
├── database.py         # Database models using SQLAlchemy
└── README.md           # Project documentation
```

---

## ⚙️ API Endpoints

### ✅ Health Check

**GET** `/health`
Check if the API is running.

**Example Response:**

```json
{
  "status": "ok",
  "message": "Server is healthy!"
}
```

---

### 📍 Get Location History

**GET** `/api/history/<location>`
Fetch location history for the specified location.

**Example:**

```
GET https://nab6wk9x0oev1u-8888.proxy.runpod.net/api/history/London
```

**Response Example:**

```json
{
  "place_name": "London",
  "timestamp": "2025-11-03T12:00:00Z",
  "description": "London is the capital of England and has rich history dating back to Roman times."
}
```

---

### 🏛️ Get Historical Places

**GET** `/api/historical_places/<location>`
Returns a list of historical sites for the given location.

**Example:**

```
GET https://nab6wk9x0oev1u-8888.proxy.runpod.net/api/historical_places/London
```

**Response Example:**

```json
[
  {
    "name": "Tower of London",
    "description": "A historic castle located on the north bank of the River Thames."
  },
  {
    "name": "Buckingham Palace",
    "description": "The London residence of the British monarch."
  }
]
```

---

## 🧠 How It Works (Backend Overview)

1. `app.py` defines Flask routes for `/health`, `/api/history/<place>`, and `/api/historical_places/<place>`.
2. When a request comes in:

   * `writer.py` uses **TavilySearch** to find relevant information about the location.
   * `utils.py` wraps Tavily’s API safely and handles exceptions.
   * Results are stored or fetched from the database via models in `database.py`.
3. The response is returned in JSON format.

---

## 🛠️ Setup Instructions

```bash
git clone https://github.com/yourusername/location-history-api.git
cd location-history-api
pip install -r requirements.txt
flask run
```

---

## 🧾 License

This project is released under the **MIT License**.

---
