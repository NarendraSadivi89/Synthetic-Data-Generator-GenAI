import streamlit as st
from data_generator import generate_data
from dotenv import load_dotenv
import os


class ChatPage:
    def __init__(
            self,
            page_title,
            page_icon,
            header
    ):
        load_dotenv()
        st.set_page_config(page_title=page_title, page_icon=page_icon)
        st.image('assets/cgi-logo.png')
        st.title("Synthetic Data Generation - Gen AI")
        st.header(header)
        uploaded_file = st.file_uploader("Upload a DB schema file (.sql)", type=["sql"])
        #print(f"uploaded_file in app.py: {uploaded_file.name}")
        db_file_path = ""
        schema_text = ""
        if st.button("Generate Test Data"):
            with st.spinner("Generating data..."):
                if uploaded_file is not None:
                    file_name_without_extension = os.path.splitext(uploaded_file.name)[0]
                    sql_file_path = os.path.join('./', uploaded_file.name)
                    db_file_path = os.path.join('./', f"{file_name_without_extension}.db")
                    if not os.path.exists(os.path.dirname(sql_file_path)):
                        st.error("Directory does not exist")
                        return
                    schema_text = uploaded_file.getvalue().decode("utf-8")
                    # with open(sql_file_path, 'w') as file:
                    #     file.write(schema_text)
                    
                    print(f"sql_file_path: {sql_file_path}")
                    print(f"db_file_path: {db_file_path}")
                    
                    try:
                        synthetic_data = generate_data(sql_file_path,db_file_path)
                        print(f"synthetic_data in ChatPage.py: {synthetic_data}")
                        st.write(synthetic_data)
                        st.write("Synthetic data for the given schema is successfully generated and can be downloaded using 'Download Test Data' button")
                        st.download_button("Download Synthetic Data", synthetic_data, "synthetic_data.sql")
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please upload a database schema file.")
                    
        # with st.spinner('Loading...'):
        #                     sql_agent = chat_provision(db_file_path)

        # st.container()
        # if prompt := st.chat_input(placeholder="Ask anything about generated synthetic data"):
        #     response = handle_chat_question(sql_agent, prompt)
        #     st.chat_message('assistant').write(response)
        #     #st.download_button("Download Synthetic Data", response, "synthetic_data.sql")
                    


if __name__ == '__main__':
    ChatPage(
        page_title="Chat",
        page_icon="🤖",
        header=""
    )

