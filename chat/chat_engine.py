from chat.sql_generator import generate_sql
from chat.db_executor import run_sql
from utils.visualization import generate_chart_if_needed

def chat_with_data(user_question, ddl_content, chat_history):
    sql_result = generate_sql(user_question, ddl_content)
    
    if sql_result["error"]:
        return {
            "user": user_question,
            "assistant": sql_result["message"],
            "sql": sql_result.get("sql"),
            "df": None,
            "chart": None,
            "error": sql_result["error"],
        }
    
    sql_query = sql_result["sql"]
    
    exec_result = run_sql(sql_query)
    
    if exec_result["error"]:
        return {
            "user": user_question,
            "assistant": f"SQL execution error: {exec_result['error']}",
            "sql": sql_query,
            "df": None,
            "chart": None,
            "error": "sql-execution",
        }
    
    df = exec_result["df"]
    
    chart_bytes = generate_chart_if_needed(user_question, df)
    
    return {
        "user": user_question,
        "assistant": "Here are the results:",
        "sql": sql_query,
        "df": df,
        "chart": chart_bytes,
        "error": None,
    }
