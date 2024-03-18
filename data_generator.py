import openai
import os
import io
import csv
import tiktoken
import sqlite3
import re
import streamlit as st
from openai import OpenAI
from io import StringIO
from langchain.agents import initialize_agent, AgentType, AgentExecutor
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def create_tables(sql_file, db_file):
    # Connect to the SQLite database
    print(f"sql_file:{sql_file}")
    print(f"db_file:{db_file}")
    conn = sqlite3.connect(db_file)
    print(f"conn:{conn}")
    cursor = conn.cursor()
    print(f"cursor:{cursor}")

    # Read SQL file
    with open(sql_file, 'r') as file:
        sql_script = file.read()
    print(f"sql_script:{sql_script}")
    # Execute the SQL script
    try:
        cursor.executescript(sql_script)
        conn.commit()
        print("Tables created successfully--")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

def extract_csv_data(csv_text):
    triple_backtick_pattern = re.compile(r'```(?:csv\s*)?(.*?)```', re.DOTALL)
    backtick_match = triple_backtick_pattern.search(csv_text)
    if backtick_match:
        csv_text = backtick_match.group(1).strip()
    else:
        return "No CSV data found"

    # Parse CSV data
    f = io.StringIO(csv_text)
    reader = csv.reader(f)
    headers = next(reader, None)  # Extract headers

    # Format data as needed for database insertion
    data = []
    for row in reader:
        if row:  # Ensure row is not empty
            formatted_row = [value.strip() for value in row]  # Remove leading/trailing whitespace
            # Add more formatting as needed based on your database schema
            data.append(formatted_row)

    return data

def get_first_table_info(db_file_path):
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    # Get the first table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ") #and name = 'Customers' ORDER BY name;")
    table_name = cursor.fetchone()[0]
    print(f"table_name:{table_name}")

    # Get the column names of the table
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"columns:{columns}")

    cursor.close()
    conn.close()
    return table_name, columns

def get_current_table_info(db_file_path, table_name):
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    # Get the first table name
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type = 'table' and name = '{table_name}';")
    table_name = cursor.fetchone()[0]
    print(f"table_name:{table_name}")

    # Get the column names of the table
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [column[1] for column in cursor.fetchall()]
    print(f"columns:{columns}")

    cursor.close()
    conn.close()
    return table_name, columns


def insert_data_into_db(csv_data, db_file_path, table_name):
    # Get the first table name and its columns
    first_table, columns = get_first_table_info(db_file_path)

    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    if first_table == table_name:
        # Create a dynamic SQL statement based on the number of columns
        placeholders = ', '.join(['?'] * len(columns))
        print(f"placeholders:{placeholders}")
        cursor.executemany(f'INSERT INTO {first_table} ({", ".join(columns)}) VALUES ({placeholders})', csv_data)
        print(f"insert successful")
    else:
        current_table, columns = get_current_table_info(db_file_path, table_name)
        placeholders = ', '.join(['?'] * len(columns))
        print(f"placeholders:{placeholders}")
        print(f"INSERT INTO {current_table} ({", ".join(columns)}) VALUES ({placeholders})")
        cursor.executemany(f'INSERT INTO {current_table} ({", ".join(columns)}) VALUES ({placeholders})', csv_data)
        print(f"insert successful")
        

    conn.commit()
    cursor.close()
    conn.close()


def generate_data(sql_file_path,db_file_path):
    context = ""
    response = ""
    total_input_tokens = 0
    total_output_tokens = 0
    input_tokens = 0
    output_tokens = 0
    
    # sql_file_path = 'insurance_domain_schema.sql'
    # db_file_path = 'insurance_domain.db'
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    if os.path.getsize(db_file_path) == 0: #not os.path.exists(db_file_path) --creates insurance_domain.db file if .db file doesn't exist or empty
        create_tables(sql_file_path, db_file_path)
        first_table, columns = get_first_table_info(db_file_path)
        base_prompt = f"""You are a synthetic data generator for a given schema.You have access to database {db_file_path}, 
    analyze the underlying schema and existing data in each of the tables and then generate synthetic data which mimics the actual data. 
    Ensure Primary Key Constraint, Foreign Key Constraint, Unique Constraint, Not Null Constraint while generating synthetic data.
    Also ensure referential integrity between tables while generating synthetic data. Skip those tables where generating additional sythentic data doesn't make any sense."""
    #Cascade Constraints, Check Constraint, Default Constraint, Index Constraint, Composite Constraint, Domain Constraint and any other constraint that you can think of
        prompt = f"""
    {base_prompt}
    Generate synthetic data of 50 rows in csv format for the {first_table} table based on the most recenlty inserted records in the {first_table} table and other tables.
    If the {first_table} table is empty then dont't bother about incrementing primary key value, just start with any value that matches the column description 
    but make sure to generate the relevant values for foreign key columns, values shall fall with in the range of most recently inserted rows in the related or dependent tables.
    If the {first_table} table has any existing data then get the max value of the primary key and then incrementally generate from the next value of the max value of the primary key to avoid UNIQUE constraint error.
    Don't include any special characters like [comma(,),single quotes('') etc.,] for the generated column values and keep it simple in your csv formatted response. 
    Enclose the csv formatted data in triple backticks like ``` (csv data goes here) ```.
    Don't explain much about how you generated the data but just summarize it in 2 lines and focus mainly on generating the synthetic data."""
        sql_agent = gen_data_provision(db_file_path)
        input_tokens = num_tokens_from_string(prompt, "cl100k_base")
        total_input_tokens += input_tokens
        print(f"prompt: {prompt}\n\n")
        response = handle_gendata_question(sql_agent, prompt)
        context += "\n" + response
        output_tokens = num_tokens_from_string(response, "cl100k_base")
        total_output_tokens += output_tokens
        csv_data = extract_csv_data(response)
        print(f"csv_data:{csv_data}")
        insert_data_into_db(csv_data, db_file_path, first_table)
        conn.commit()
#else:
    first_table, columns = get_first_table_info(db_file_path)
    # Fetch the list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    row_counter = 0
    table_counter = 0
    tables_with_zero_rows = []
    # Iterate over the tables and get the count of records in each
    for table in tables:
        table_name = table[0]  # Extract the table name from the tuple
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if cursor.fetchone()[0] == 1:
            table_counter += 1
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]  # Fetch the count
        if count == 0:
            tables_with_zero_rows.append(table_name) 
        if count > 0:
            row_counter += 1
        print(f"Table {table_name} has {count} records.")
    print("Tables with zero rows:", tables_with_zero_rows)
    print(f"row_counter {row_counter} and {table_counter} table_counter.")
    # Construct the WHERE condition for tables_with_zero_rows
    where_condition = " OR ".join([f"name = '{table}'" for table in tables_with_zero_rows])
    #After all the tables are populated with the data, need to consider first table for synthetic data generation
    if row_counter == table_counter:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    else:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type = 'table' and ({where_condition})") #and name = 'Customers' ORDER BY name;")
        
    table_names = cursor.fetchall()
    base_prompt = f"""You are a synthetic data generator for a given schema.You have access to database {db_file_path}, 
    analyze the underlying schema and existing data in each of the tables and then generate synthetic data which mimics the actual data.
    Ensure Primary Key Constraint, Foreign Key Constraint, Unique Constraint, Not Null Constraint while generating synthetic data. 
    Also ensure referential integrity between tables while generating synthetic data. Skip those tables where generating additional sythentic data doesn't make any sense."""
    #, Cascade Constraints, Check Constraint, Default Constraint, Index Constraint, Composite Constraint, Domain Constraint and any other constraint that you can think of
    sql_agent = gen_data_provision(db_file_path)
    for table in table_names:
        table_name = table[0] 
        prompt = f"""
    {base_prompt}
    Generate synthetic data of 50 rows for {table_name} table in csv format based on the most recenlty inserted records in the {table_name} table and other tables.
    If the {table_name} table is empty then dont't bother about incrementing primary key value, just start with any value that matches the column description
    but make sure to generate the relevant values for foreign key columns, values shall fall with in the range of most recently inserted rows in the related or dependent tables.
    If the {table_name} table has any existing data then get the max value of the primary key and then incrementally generate from the next value of the max value of the primary key to avoid UNIQUE constraint error.
    Don't include any special characters like [comma(,),single quotes('') etc.,] for the generated column values and keep it simple in your csv formatted response.
    Enclose the csv formatted data in triple backticks like ``` (csv data goes here) ```.
    Don't explain much about how you generated the data but just summarize it in 2 lines and focus mainly on generating the synthetic data."""
        print(f"prompt:{prompt}")
        
        input_tokens = num_tokens_from_string(prompt, "cl100k_base")
        total_input_tokens += input_tokens
        #print(f"prompt: {prompt}\n\n")
        
        response = handle_gendata_question(sql_agent, prompt)
        context += "\n" + response
        
        output_tokens = num_tokens_from_string(response, "cl100k_base")
        total_output_tokens += output_tokens
        try:
            csv_data = extract_csv_data(response)
            print(f"csv_data:{csv_data}")
            insert_data_into_db(csv_data, db_file_path, table_name)
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            conn.commit()

    print(f"Input tokens: {total_input_tokens}, Output tokens: {total_output_tokens}, Total tokens: {total_input_tokens + total_output_tokens}")
    #print(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}, Total tokens: {input_tokens + output_tokens}")
    conn.commit()
    cursor.close()
    conn.close()
    
    try:
        with open(db_file_path, "w") as file:
            file.truncate(0)
            print(f"Contents of {db_file_path} have been emptied.")
    except Exception as e:
        print(f"Error: Unable to empty {db_file_path} - {e}")
    return context

def handle_chat_question(sql_agent, prompt, attempt = 1):
    st.chat_message('user').write(prompt)

    with st.spinner("Thinking..."):
        response = ""
        try:
            response = sql_agent.run(
                f"""{prompt}
                """)
        except Exception as e:
            response = "I don't know"
            
        if "I don't know" in response and attempt < 3:
            return handle_chat_question(sql_agent, prompt, attempt + 1)
        
        #st.write(f"From {db_file_path}:\n\n")
        return response

def handle_gendata_question(sql_agent, prompt, attempt = 1):
    #st.chat_message('user').write(prompt)

    with st.spinner("Thinking..."):
        response = ""
        try:
            response = sql_agent.run(
                f"""{prompt}
                """)
        except Exception as e:
            response = "I don't know"
            
        if "I don't know" in response and attempt < 3:
            return handle_gendata_question(sql_agent, prompt, attempt + 1)
        
        #st.write(f"From {db_file_path}:\n\n")
        return response
    

def gen_data_provision(db_file_path):
    llm = ChatOpenAI(model='gpt-4-0125-preview',temperature=1)
    #conn = sqlite3.connect(f"{db_file_path}")
    db = SQLDatabase.from_uri(f"sqlite:///./{db_file_path}")
    agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
    return agent_executor

# def chat_provision(db_file_path):
#     llm = ChatOpenAI(model='gpt-4-0125-preview',temperature=1)
#     #conn = sqlite3.connect(f"{db_file_path}")
#     db = SQLDatabase.from_uri(f"sqlite:///./{db_file_path}")
#     agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
#     return agent_executor

# def call_llm(prompt):
#     try:
#         response = openai.chat.completions.create(
#             model="gpt-4-0125-preview", #gpt-4-turbo-preview #gpt-3.5-turbo-0613
#             messages=[
#             {"role": "system", "content": "You are a synthetic data generator for a given database schema with multiple tables."},
#             {"role": "user", "content": prompt}
#         ],
#             temperature=0.9
#             #max_tokens=4096
#         )
#         return response.choices[0].message.content.strip() if response.choices else ""
#     except Exception as e:
#         return f"Error generating data: {e}"    

        


        