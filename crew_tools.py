# crew_tools.py (Monolith Backend + Streamlit UI)
import os
import streamlit as st
import snowflake.connector
import openai
from crewai import Crew
import requests

# --- CrewAI Setup ---
crew = Crew()

@crew.tool
def query_ledger(start_date: str, end_date: str):
    """
    Return sums of AMOUNT per GL_ACCOUNT from GL_LEDGER_BASE
    between start_date and end_date (inclusive).
    DB: RAIDER_DB
    SCHEMA: SQL_SERVER_DBO
    Dates should be in YYYY-MM-DD format.
    """
    conn = snowflake.connector.connect(
       account=os.environ["SF_ACCOUNT"],
       user=os.environ["SF_USER"],
       password=os.environ["SF_PASS"],
       warehouse=os.environ["SF_WH"],
       database="RAIDER_DB",
       schema="SQL_SERVER_DBO"
    )
    cur = conn.cursor()
    cur.execute(f"""
      SELECT
        GL_ACCOUNT,
        SUM(AMOUNT) AS TOTAL_AMOUNT
      FROM GL_LEDGER_BASE
      WHERE POSTING_DATE BETWEEN '{start_date}' AND '{end_date}'
      GROUP BY GL_ACCOUNT
      ORDER BY TOTAL_AMOUNT DESC
      LIMIT 50
    """)
    return cur.fetchall()

@crew.tool
def call_foundry(fn: str, **kwargs):
    """Invoke a Foundry function via HTTP."""
    resp = requests.get(
      f"https://foundry.mycompany.com/{fn}",
      params=kwargs,
      headers={"Authorization":f"Bearer {os.environ['FOUNDRY_TOKEN']}"}
    )
    return resp.json()

@crew.tool
def llm_chat(prompt: str):
    """Fallback to ChatGPT for general questions."""
    openai.api_key = os.environ["OPENAI_KEY"]
    r = openai.ChatCompletion.create(
      model="gpt-4",
      messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content

crew.run_agent(
  name="financial_assistant",
  system_prompt="""
    You are FinanceBot. You have three tools:
    1) query_ledger(start_date, end_date)
    2) call_foundry(fn, **kwargs)
    3) llm_chat(prompt)

    Use query_ledger for GL summaries.
    Use call_foundry for external Foundry functions.
    Use llm_chat for any general Q&A or formatting tasks.
  """
)

# --- Streamlit UI ---
st.set_page_config("FinanceBot", layout="wide")
st.title("💸 FinanceBot — Ask Your Ledger")

if "history" not in st.session_state:
    st.session_state["history"] = []

user_input = st.chat_input("Ask about P&L, KPIs, GL accounts…")
if user_input:
    st.session_state.history.append(("user", user_input))
    response = llm_chat(user_input)
    st.session_state.history.append(("bot", response))

for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)
