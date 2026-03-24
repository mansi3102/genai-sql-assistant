# 🤖 GenAI SQL Assistant  
### Ask questions. Get SQL. Make decisions — instantly.

---

## Why GenAI Assistant?

Most teams sit on a wealth of data locked inside databases, spreadsheets, and data warehouses. Getting answers still requires writing SQL, and understanding the quirks of each system.


- Ask a question in plain English → get a human-readable answer backed by real SQL
- Works with **any database**: SQLite, PostgreSQL, MySQL, or any SQLAlchemy-compatible store
- Works with **flat files**: load CSV and Excel files and query them with full JOIN support across multiple files
- Goes beyond naive text-to-SQL with **four layers of context enrichment**: schema descriptions, business rules, example query patterns, and accumulated learnings from past corrections
- **Self-corrects** when generated SQL fails — retries up to N times, learns from the fix, and remembers it for next time


## ⚙️ Key Features

✅ Natural Language → SQL conversion (LLM-powered)  
✅ Auto SQL error correction (self-learning memory)  
✅ Smart visualizations (charts based on data)  
✅ Works with CSV, Excel, or SQLite  
✅ Interactive Streamlit UI  
✅ Business insight generation (non-technical explanations)

---

## Design & Architecture

### The Inspiration

> *"The agent lets employees go from question to insight in minutes, not days. This lowers the bar to pulling data and nuanced analysis across all functions, not just by the data team."*

This project captures the core concepts in a **minimal, self-sufficient** anyone can run locally:

- A realistic business use case with 4–5 related tables
- Context-grounded SQL generation (not naive text-to-SQL)
- A self-correction loop that fixes broken queries
- A learning system that remembers past mistakes
- A conversational interface

### The Agent Loop

Every question passes through this flow. Two LLM calls per question: one to generate SQL (deterministic), and one to synthesize a human-readable answer from the results (slightly creative).

![Agent Loop](https://github.com/user-attachments/assets/c193548c-7681-430f-8f96-423e32dc6fee)

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Groq (Llama 3.1)
- SQLite
- Pandas
- Plotly

---
### Project Structure

```

├── START_HERE          # Windows BAT file (easy to use for non technical users)
├── app.py              # Main Streamlit app
├── launcher.py         # Easy startup script
├── requirements.txt    # Dependencies
├── ecommerce_india.db  # Sample database
├── GenAI_SQL_Assistant.ipynb  # Jupyter notebook script (For building the core)
└── README.md           # How to run the project

```

## Environment Variables

### LLM API Keys

| Variable | Description | Example |
|---|---|---|
| `LLM_MODEL` | Set as Default model | `groq/llama-3.3-70b-versatile` |

## How to Run the project: 

- After setting up the folder with all the files
<img width="877" height="585" alt="Screenshot 2026-03-25 011407" src="https://github.com/user-attachments/assets/1cb1037f-eb70-4aba-8757-834b1fc0b49e" />


- Double click the BAT file (Windows Batch File)

<img width="1466" height="735" alt="BAT_ss" src="https://github.com/user-attachments/assets/9e9cd771-dfe9-4d74-bfee-cf33ea72c278" />

- Paste your Groq API Key and ask any Question such as : Which regions in India spent the most on online orders?

<img width="1891" height="956" alt="Paste_API" src="https://github.com/user-attachments/assets/80bc6e1a-8777-400b-b716-dc27757047e0" />


**Output:**
- SQL Query generated  
- Data retrieved  
- Chart displayed  
- Business insight generated  

<img width="1885" height="868" alt="SQL_query" src="https://github.com/user-attachments/assets/611b4975-3561-4941-ad99-0a400c392690" />

<img width="1873" height="848" alt="Charts_displayed" src="https://github.com/user-attachments/assets/0efcc371-3ca7-4b5f-8707-1999c19065a4" />

---

## Future Improvements

- Role-based access control
- Query validation layer
- Query history dashboard
- Dashboard saving










