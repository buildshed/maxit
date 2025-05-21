
### Agent 1: Agent with custom tools 
- `get_ticker_given_name`
- `get_latest_filings`
- `get_income_statement`

### Agent 2: Agent with custom tools, websearch and human in the loop

+ tools -> balance sheet, cash flow stmnt, tavily web search (DONE)
Human in the loop: 
- If number of tickers found > 1, then ask the human which one. 


### Agent 3: State, Peer Comparison 
Router Logic 

### Agent 4: LT memory 
- Agent has memory about its peers 
- At the end of a conversation, memory is updated,as applicable 

MVP-1: As a simple repo that runs on laptop using `langgraph dev`)
1. ChatUI: Agent UI (https://agentchat.vercel.app/)
2. Agent Orchestration Framework: Langgraph 
3. Agents: 
    1 'Planner Layer' Agent: RM Agent
    1 'Agent Layer' Agent - SEC Filings Agent, Equity Snapshot Agent, News Agent
4. Tools ('Tooling Layer')
    a) Data Pipelines: None
    b) Execution Tools: 
    SEC Filings Agent: web search, get_ticker_given_name, get_cik, get_latest_filings,  get_financial_statement (cash flow, bs, income statement)
    Equity Snapshot Agent: get_earnings, get_analyst_rating_summary, get_stock_quote
    News Agent: get_news(ticker) 
    c) Memory Tools: save_client_memory, get_client_info, update_client_info
    d) Observability Tools: 
    e) Policy & Governance Tools: None 
    f) Action Tools: None 
    g) Utility (Common) Tools
5. Actions - None 
6. Data - SEC Filings 
7. Memory: 
    Short term DONE
    - `messages` construct of langgraph 
    Long term DONE (agent5)
    - `Inmemory` 
    - Namespaces: `client`
        client: [client name, ticker(s), {peers: dict of name, ticker}, {saved_analysis: analysisname, exec_date and time, Output: (link)}
8. Intervention & Oversight: (e..g Human in the Loop) - None 
9. Observability - Langgraph Studio 
10. Pre-defined Frameworks: 1- Peer Comparison framework (as a prompt)
10a. Tasks - None 
10b. Blueprints: None 
11. Reasoning: Chatbot -> Tools -> Save or Update Memory (optional) 
12. Router -None. Needed in multi agent architecture  
13. Security - None 
14. Evaluation - None
        
    