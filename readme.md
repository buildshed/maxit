
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

MVP-1: 

(as a simple repo that runs on laptop)
1. Front End: Langraph Studio DONE
3. Memory: Short term DONE
    - `messages` construct of langgraph 
4. memory: Long term DONE (agent5)
    - `Inmemory` 
    - Namespaces: `client`, `relationship`
        client: [client name, ticker(s), {peers: dict of name, ticker}, {saved_analysis: analysisname, exec_date and time, Output: (link)}
5. Human in the loop: 
    - Multiple tickers found 
    - Save to LT memory 
5. Actions: 
    - Save to  LT memory (client namespace) 
6. Shared Services : 
    - Utility Tools - get bal sheet, cash flow, income statement, get ticker (from external), show tools (get str of all tools), web search
    - Memory - save analysis to LT, get analysis from LT, get peers, save peers, get ticker (from memory), save ticker
7. Reasoning Framework: 
    - START 
    - Chatbot with tools 
    - Update memory (if needed)
    - END 

    