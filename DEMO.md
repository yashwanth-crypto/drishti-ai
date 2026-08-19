# Drishti-AI — demo recording script

A ~2½ minute screen recording for people who aren't in the room. Every number
below is real; nothing here is staged.

---

## Before you hit record

**1. Start all three services** (Postgres runs as a Windows service already):

```powershell
# terminal 1 — inference
cd C:\dev\drishti-ai\app\inference
..\..\.venv\Scripts\python.exe -m uvicorn main:app --port 8000

# terminal 2 — backend
cd C:\dev\drishti-ai\app\backend
& "C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot\bin\java.exe" -jar target\drishti-backend-1.0.0.jar

# terminal 3 — dashboard
npm run dev --prefix C:\dev\drishti-ai\dashboard
```

Wait until `http://localhost:8080/actuator/health` says `UP`.

**2. Open `C:\dev\drishti-ai\demo_images\` in Explorer** and park it beside the
browser. Four parts, already checked:

| File | What the model says |
|---|---|
| `1-good-part.jpeg` | PASS, 99.7% |
| `2-defective-part.jpeg` | FAIL, 100% |
| `3-defective-part.jpeg` | FAIL, 100% |
| `4-good-part.jpeg` | PASS, 98.5% |

**3. Housekeeping**

- Browser at ~100% zoom, full screen, close other tabs
- Sign out first so the recording starts at the login screen
- Threshold should be **0.5** (Settings tab)
- `Win + Alt + R` starts Windows' built-in recorder

---

## The script

### 0:00 — Log in *(15s)*

Start on the login screen.

> "Drishti-AI is a quality-inspection system for small manufacturers. It runs
> entirely on one computer on the shop floor — no cloud, no internet."

Log in as **`owner`** / `drishti-owner`.

### 0:15 — Overview *(25s)*

> "Four models behind one dashboard: defect detection, Hindi alerts for the
> operator, tool-wear prediction, and demand forecasting."

Point at the tiles — 24 inspections, 99.4% test accuracy, tool alerts.

> "The 99.4% is measured on a held-out test set of real castings from a foundry
> in Rajkot — 715 images the model never trained on."

### 0:40 — The live inspection ⭐ *(50s)*

**This is the demo. Spend the most time here.**

Go to **Inspect a Part**. Drag in `2-defective-part.jpeg`.

> "That's a real photo of a cast part, going through the model right now."

Let the result land. Point at it:

> "Rejected, 100% confidence, five milliseconds. And this line is the point —"

Read out the Hindi alert:

> "— the operator gets told in Hindi: part rejected, surface defect found, set it
> aside and show the quality inspector. Most shop-floor operators in India don't
> read English error codes. That's why the alert isn't in English."

Now drag in `1-good-part.jpeg`.

> "And a good part passes — same speed, different instruction: send it on."

### 1:30 — The threshold *(35s)*

Go to **Settings**.

> "A missed defect costs far more than a false alarm. So the owner can decide how
> confident the model has to be before a part is allowed through."

Drag the defect threshold to about **0.99**, save. Go back to **Inspect a Part**,
drag in `4-good-part.jpeg` (98.5% — just under the bar).

> "Same part, but now the model isn't confident enough, so instead of passing it,
> it goes to a human. A defective part still fails no matter what — the setting
> can only ever make it stricter, never laxer."

**Put the threshold back to 0.5 before moving on.**

### 2:05 — The feedback loop *(25s)*

Go to **Quality Inspection**. Point at the correct/wrong buttons.

> "When the model gets one wrong, the operator says so."

Click **wrong** on any row.

> "That stores the operator's own label next to the image. Over a pilot that
> becomes training data from this specific shop — which nobody else has."

### 2:30 — Close *(15s)*

Click through **Predictive Maintenance** and **Demand Forecasting** while talking.

> "Same system also predicts tool wear from vibration and current sensors, and
> forecasts demand per product category. All of it on one box, offline."

---

## After recording

Undo the demo edits so the app is clean for next time:

- Settings → threshold back to **0.5**
- The feedback you clicked stays recorded — that's fine, it's real

---

## Numbers you can be asked about

Every one of these is measured, not estimated:

| Claim | Where it comes from |
|---|---|
| 99.4% defect accuracy | mean over 3 seeds; deployed model scores 99.30% on the 715-image held-out set |
| ~5 ms per inspection | measured on an RTX 5060; the paper's stated target was under 2 seconds |
| 19.7% demand WAPE | held-out weeks, 28 product categories |
| Tool-wear RUL | trained on the Piecuch & Żabiński 2025 milling dataset, split by physical tool |

**Be straight about the limits if asked** — it plays better than dodging:

- The casting dataset is real industrial data, but castings, not CNC-turned parts
- Sensor and camera input is replayed from recorded data, not live hardware
- No pilot deployment yet
