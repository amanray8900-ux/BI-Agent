import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

load_dotenv("apis.env")

try:
    MONDAY_API_TOKEN = st.secrets["MONDAY_API_TOKEN"]
    CEREBRAS_API_KEY = st.secrets["CEREBRAS_API_KEY"]
except:
    MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
    CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")

# ── Monday.com API ──────────────────────────────────────────
def monday_query(graphql_query, variables={}):
    try:
        response = requests.post(
            "https://api.monday.com/v2",
            headers={
                "Authorization": MONDAY_API_TOKEN,
                "Content-Type": "application/json",
                "API-Version": "2024-01"
            },
            json={"query": graphql_query, "variables": variables},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def list_boards():
    query = "query { boards(limit: 20) { id name } }"
    data = monday_query(query)
    return data.get("data", {}).get("boards", [])

def get_board_items(board_id):
    query = """
    query ($boardId: ID!) {
      boards(ids: [$boardId]) {
        name
        columns { id title type }
        items_page(limit: 400) {
          items {
            id name
            column_values { id text column { title } }
          }
        }
      }
    }
    """
    data = monday_query(query, {"boardId": board_id})
    board = data.get("data", {}).get("boards", [{}])[0]
    items = board.get("items_page", {}).get("items", [])

    records = []
    for item in items:
        record = {"name": item["name"]}
        for cv in item.get("column_values", []):
            col_name = cv["column"]["title"].lower().replace(" ", "_")
            value = cv["text"]
            if value:
                value = value.strip()
                value = value.replace("$", "").replace(",", "")
                if value.lower().endswith("k"):
                    try:
                        value = float(value[:-1]) * 1000
                    except:
                        pass
            record[col_name] = value if value else None
        records.append(record)

    return {"board_name": board.get("name"), "total": len(records), "data": records}

# ── Tool Definitions ────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_boards",
            "description": "List all available monday.com boards",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_board_data",
            "description": "Fetch all data from a monday.com board by name. Use this for any business question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "board_name": {
                        "type": "string",
                        "description": "Name of the board e.g. 'Deals' or 'Work Orders'"
                    }
                },
                "required": ["board_name"]
            }
        }
    }
]

# ── Tool Execution ──────────────────────────────────────────
def execute_tool(tool_name, tool_input):
    if tool_name == "list_boards":
        boards = list_boards()
        return json.dumps(boards)

    if tool_name == "fetch_board_data":
        boards = list_boards()
        name = tool_input.get("board_name", "").lower()
        board = next((b for b in boards if name in b["name"].lower()), None)

        if not board:
            return json.dumps({
                "error": "Board not found",
                "available": [b['name'] for b in boards]
            })

        result = get_board_items(board["id"])
        return json.dumps(result)

# ── Cerebras Agent ──────────────────────────────────────────
def run_agent(user_message, chat_history, action_log):
    client = Cerebras(api_key=CEREBRAS_API_KEY)

    system_prompt = """
You are a Business Intelligence assistant for company leadership.

Rules:
- Always fetch live data from monday.com using tools before answering.
- Never guess numbers.
- Provide concise executive insights.

When analyzing data:
1. Summarize key metrics
2. Identify trends or patterns
3. Highlight risks or missing data
4. Provide actionable insights
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages += chat_history
    messages.append({"role": "user", "content": user_message})

    action_log.append("🧠 Understanding the business question")

    while True:
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model="gpt-oss-120b",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=4096
                )
                break
            except Exception as e:
                if attempt < 2:
                    action_log.append(f"⏳ Retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    raise e

        msg = response.choices[0].message
        tool_calls = msg.tool_calls

        if not tool_calls:
            final_text = msg.content
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": final_text})
            return final_text, chat_history

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in tool_calls
            ]
        })

        for tc in tool_calls:
            tool_name = tc.function.name
            tool_input = json.loads(tc.function.arguments)

            action_log.append(f"📡 Fetching live data from monday.com")
            action_log.append(f"🔧 Calling: **{tool_name}** with `{tool_input}`")

            result = execute_tool(tool_name, tool_input)
            result_data = json.loads(result)

            if "total" in result_data:
                action_log.append(f"📊 Analyzing business data")
                action_log.append(f"📦 Got **{result_data['total']} items** from **{result_data['board_name']}**")
            elif isinstance(result_data, list):
                action_log.append(f"📋 Found **{len(result_data)} boards**")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })

# ── Streamlit UI ────────────────────────────────────────────
st.set_page_config(page_title="Monday.com BI Agent", layout="wide")
st.title("📊 Monday.com Business Intelligence Agent")
st.markdown("""
**Example questions you can ask:**
- How is our pipeline looking this quarter?
- Show top deals by value
- Which sector has the most revenue?
- Are there any delayed work orders?
""")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "messages_display" not in st.session_state:
    st.session_state.messages_display = []
if "action_logs" not in st.session_state:
    st.session_state.action_logs = []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Chat")

    for msg in st.session_state.messages_display:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask anything about your business data...")

    if user_input:
        st.session_state.messages_display.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Querying monday.com..."):
                action_log = []
                answer, updated_history = run_agent(
                    user_input,
                    st.session_state.chat_history,
                    action_log
                )
                st.session_state.chat_history = updated_history
                st.session_state.action_logs.extend(action_log)
                st.session_state.messages_display.append({"role": "assistant", "content": answer})
                st.markdown(answer)

with col2:
    st.subheader("🔍 Action Log")
    if st.session_state.action_logs:
        for log in st.session_state.action_logs[::-1]:
            st.markdown(log)
    else:
        st.caption("Tool calls will appear here when you ask a question.")
