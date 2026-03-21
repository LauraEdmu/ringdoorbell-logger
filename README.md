# Ring Logger

Simple FastAPI webhook service to log **Ring (IFTTT) events → PostgreSQL**.

---

## **Stack**

- FastAPI + Uvicorn
- psycopg
- PostgreSQL
- python-dotenv

---

## **Setup**

### **Install**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn psycopg[binary] python-dotenv
````

---

### **.env**

```env
DATABASE_URL=postgresql://laura:password@localhost:5432/ring
WEBHOOK_SECRET=your-secret
```

---

### **Database**

```sql
CREATE TABLE ring_events (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL DEFAULT 'ifttt',
    event_type TEXT NOT NULL,
    device_name TEXT,
    occurred_at TIMESTAMPTZ,
    payload JSONB NOT NULL,
    dedupe_key TEXT UNIQUE
);
```

---

### **Run**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Endpoint:

```text
POST /ring-event
```

---

## **IFTTT Config**

**Action:** Webhooks → Make a web request

* **URL**

  ```
  http://YOUR_SERVER:8000/ring-event
  ```

* **Method**

  ```
  POST
  ```

* **Content-Type**

  ```
  application/json
  ```

* **Header**

  ```
  X-Webhook-Secret: your-secret
  ```

---

### **Ring applet body**

```json
{
  "event_type": "ring",
  "device_name": "{{DoorbellName}}",
  "occurred_at": "{{CreatedAt}}"
}
```

### **Motion applet body**

```json
{
  "event_type": "motion",
  "device_name": "{{DoorbellName}}",
  "occurred_at": "{{CreatedAt}}"
}
```

---

## **Example queries**

```sql
SELECT id, event_type, device_name, occurred_at
FROM ring_events
ORDER BY id DESC
LIMIT 10;
```

```sql
SELECT event_type, COUNT(*) FROM ring_events GROUP BY event_type;
```

---

## **Notes**

* IFTTT only provides:

  * `DoorbellName`
  * `CreatedAt`
* Timestamp is parsed from strings like:

  ```
  March 21, 2026 at 11:57AM
  ```
* Raw data is always stored in `payload`

