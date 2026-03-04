# 📊 Monday.com Business Intelligence Agent

A conversational AI agent that answers founder-level business intelligence queries by connecting live to Monday.com boards containing Work Orders and Deals data.

🔗 **Live App:** [your-app-link.streamlit.app](https://your-app-link.streamlit.app)
🔗 **Monday.com Board:** [your-monday-board-link](https://your-monday-board-link)

---

## Architecture Overview

```
User (Browser)
      ↓
Streamlit Chat UI
      ↓
Cerebras LLM (gpt-oss-120b via Tool Calling)
      ↓
Tool Execution Layer
      ↓
Monday.com GraphQL API (Live, per query)
  ├── Work Order Tracker Board
  └── Deal Tracker Board
```

### How it works

1. User types a business question in the chat
2. The Cerebras LLM (gpt-oss-120b) interprets the question and decides which Monday.com board to query
3. The tool execution layer makes a live GraphQL API call to Monday.com
4. Raw board data is fetched, normalized, and passed back to the LLM
5. The LLM analyzes the data and returns a business insight
6. Every API call is visible in the Action Log panel on the right side of the UI

### Key Components

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app — UI, agent loop, Monday.com API calls |
| `requirements.txt` | Python dependencies |
| `apis.env` | Local environment variables (not committed to GitHub) |

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| UI | Streamlit | Fast to build, easy to deploy, Python-native |
| LLM | Cerebras (gpt-oss-120b) | Free tier, high rate limits, fast inference, supports tool calling |
| Data Source | Monday.com GraphQL API | Live data per query, no caching |
| Hosting | Streamlit Cloud | Free, connects directly to GitHub |

---

## Monday.com Configuration

### Step 1: Create a Monday.com account
Go to [monday.com](https://monday.com) and sign up for a free account.

### Step 2: Import the Work Orders board
1. Download the Work Orders CSV from the provided Google Sheet
2. In Monday.com, click **+** in the left sidebar → **Import data** → **Excel/CSV**
3. Upload the CSV and name the board **"Work Orders"**

### Step 3: Import the Deals board
1. Download the Deals CSV from the provided Google Sheet
2. Repeat the same import process
3. Name the board **"Deals"**

### Step 4: Get your API token
1. Click your profile picture (top left) → **Administration** → **API**
2. Copy your **Personal API Token**

### Step 5: Get your Board IDs
1. Click on the Work Orders board
2. Copy the number from the URL: `https://yourworkspace.monday.com/boards/XXXXXXXXXX`
3. Repeat for the Deals board

---

## Local Setup Instructions

### Prerequisites
- Python 3.10 or higher
- A Monday.com account with both boards imported
- A Cerebras API key (free at [cloud.cerebras.ai](https://cloud.cerebras.ai))

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/amanray8900-ux/BI-Agent.git
cd BI-Agent
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Create your `apis.env` file:**
```
MONDAY_API_TOKEN=your_monday_api_token_here
CEREBRAS_API_KEY=your_cerebras_api_key_here
```

**4. Run the app:**
```bash
streamlit run app.py
```

**5. Open your browser at:** `http://localhost:8501`

---

## Deployment (Streamlit Cloud)

1. Push code to GitHub (ensure `apis.env` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file as `app.py`
5. Add secrets under **Settings → Secrets**:
```toml
MONDAY_API_TOKEN = "your_monday_token_here"
CEREBRAS_API_KEY = "your_cerebras_key_here"
```
6. Click **Deploy**

---

## Example Queries

- *"How is our pipeline looking this quarter?"*
- *"Show top 5 deals by value"*
- *"Which sector has the most revenue?"*
- *"Are there any delayed work orders?"*
- *"Compare energy sector deals with tech sector"*
- *"How many work orders are currently in progress?"*

---

## Features

- **Live Monday.com data** — every query fetches fresh data, no caching
- **Tool call transparency** — Action Log panel shows every API call made
- **Data normalization** — handles messy data, missing values, inconsistent formats
- **Multi-turn conversations** — follow-up questions build on prior context
- **Cross-board queries** — can analyze both Work Orders and Deals together

---

## Dependencies

```
streamlit
requests
python-dotenv
cerebras-cloud-sdk
```
