from database.db_setup import execute_query

def run_sql(sql):
    try:
        df = execute_query(sql)
        return {"df": df, "error": None}
    except Exception as e:
        return {"df": None, "error": str(e)}
