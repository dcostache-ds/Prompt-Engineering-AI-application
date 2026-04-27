from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
from generator.ddl_parser import parse_ddl
from generator.data_generator import generate_synthetic_data, apply_textual_edit
from chat.chat_engine import chat_with_data
from database.db_setup import test_connection, save_to_db
from utils.file_utils import create_zip
st.set_page_config(page_title="Data Assistant", layout="wide")

def _init_state():
    if "generated_data" not in st.session_state:
        st.session_state.generated_data = {}
    if "ddl_content" not in st.session_state:
        st.session_state.ddl_content = ""
    if "table_names" not in st.session_state:
        st.session_state.table_names = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

_init_state()  

if "generated_data" not in st.session_state:
    st.session_state.generated_data = {}

if "ddl_content" not in st.session_state:
    st.session_state.ddl_content = ""

if "table_names" not in st.session_state:
    st.session_state.table_names = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
    st.title(" Data Assistant")
    st.divider()
    
    page = st.radio("Navigation", [" Data Generation", " Talk to your data"], label_visibility="collapsed")
    
    st.divider()
    
    db_ok = test_connection()
    if db_ok:
        st.success("● Database connected")
    else:
        st.warning("● Database offline")

if page == " Data Generation":
    st.header("Synthetic Data Generation")
    
    uploaded = st.file_uploader("Upload DDL Schema", type=["sql", "txt", "ddl"])
    
    if uploaded:
        ddl = uploaded.read().decode("utf-8")
        st.session_state.ddl_content = ddl
        
        info = parse_ddl(ddl)
        st.session_state.table_names = info["table_names"]
        
        with st.expander("Preview DDL"):
            st.code(ddl, language="sql")
        
        st.success(f"Schema uploaded: {len(info['table_names'])} tables")
    
    prompt = st.text_area("Prompt (optional)", placeholder="Ex: Generate 100 rows", height=80)
    
    with st.expander("Advanced"):
        c1, c2 = st.columns(2)
        with c1:
            temp = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        with c2:
            tokens = st.number_input("Max Tokens", 1000, 16000, 8192, 1000)
    
    if st.button("Generate", type="primary", disabled=not st.session_state.ddl_content):
        if not st.session_state.ddl_content:
            st.warning("Upload DDL first")
        else:
            with st.spinner("Generating..."):
                try:
                    dfs = generate_synthetic_data(st.session_state.ddl_content, prompt, temp, int(tokens))
                    st.session_state.generated_data = dfs
                    
                    if db_ok:
                        for name, df in dfs.items():
                            save_to_db(df, name)
                        st.info("Saved to database")
                    
                    st.success(f"Generated {len(dfs)} tables")
                except ValueError as e:
                    st.error(f"Security alert: {e}")
                except Exception as e:
                    st.error(f"Failed: {e}")
    
    if st.session_state.generated_data:
        st.divider()
        st.subheader("Preview")
        
        if st.button("Download ZIP"):
            zip_data = create_zip(st.session_state.generated_data)
            st.download_button("Download", zip_data, "data.zip", "application/zip")
        
        tabs = st.tabs(list(st.session_state.generated_data.keys()))
        
        for tab, (name, df) in zip(tabs, st.session_state.generated_data.items()):
            with tab:
                st.dataframe(df, use_container_width=True, height=300)
                st.caption(f"{len(df)} rows")
                
                csv = df.to_csv(index=False).encode()
                st.download_button(f"Download {name}.csv", csv, f"{name}.csv", "text/csv", key=f"dl_{name}")
                
                st.write("**Edit**")
                c1, c2 = st.columns([4, 1])
                
                with c1:
                    edit = st.text_input("Edit instruction", placeholder="Ex: Set 20% null", key=f"edit_{name}", label_visibility="collapsed")
                
                with c2:
                    if st.button("Apply", key=f"apply_{name}"):
                        if edit:
                            with st.spinner("Editing..."):
                                try:
                                    new_df = apply_textual_edit(df, name, edit)
                                    st.session_state.generated_data[name] = new_df
                                    if db_ok:
                                        save_to_db(new_df, name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")

elif page == " Talk to your data":
    st.header("Talk to your data")
    
    if not st.session_state.ddl_content:
        st.warning("No schema loaded")
        st.stop()
    
    if not db_ok:
        st.error("Database not connected")
        st.stop()
    
    for msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(msg["user"])
        
        with st.chat_message("assistant", avatar="🤖"):
            if msg.get("error") == "off-topic":
                st.warning(msg["assistant"])
            else:
                if msg.get("assistant"):
                    st.write(msg["assistant"])
                
                if msg.get("sql"):
                    with st.expander("Generated SQL", expanded=True):
                        st.code(msg["sql"], language="sql")
                
                if msg.get("df") is not None and not msg["df"].empty:
                    st.dataframe(msg["df"], use_container_width=True)
                    st.caption(f"{len(msg['df'])} rows")
                
                if msg.get("chart"):
                    st.image(msg["chart"])
    
    user_input = st.chat_input("Ask a question...")
    
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = chat_with_data(user_input, st.session_state.ddl_content, st.session_state.chat_history)
            
            if result.get("error") == "off-topic":
                st.warning(result["assistant"])
            else:
                if result.get("assistant"):
                    st.write(result["assistant"])
                
                if result.get("sql"):
                    with st.expander("Generated SQL", expanded=True):
                        st.code(result["sql"], language="sql")
                
                if result.get("df") is not None and not result["df"].empty:
                    st.dataframe(result["df"], use_container_width=True)
                
                if result.get("chart"):
                    st.image(result["chart"])
        
        st.session_state.chat_history.append(result)
    
    if st.session_state.chat_history:
        if st.button("Clear conversation"):
            st.session_state.chat_history = []
            st.rerun()
