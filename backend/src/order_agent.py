import autogen
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from typing_extensions import Annotated
from langchain.prompts import PromptTemplate
import psycopg2
import os
import sqlite3

os.environ["OPENAI_API_KEY"] = ""

# load env variables
load_dotenv()

query_maker_gpt_system_prompt = '''You are SQL Query Generator. Kindly generate the sql query only and use only the listed columns in 
below schema. Use only the columns available in the Schema below. 

Below is the Schema of the available tables to make the sql queries. Create and return only one query.

CREATE TABLE IF NOT EXISTS dishes (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL UNIQUE,
quantity INTEGER NOT NULL


only use the above mentioned columns in making sql query.
User Input: 
'''

admin_prompt = "Admin"
assistant_agent_prompt = '''
Do not change user input. You have the opportunity to advise the Admin on selecting the appropriate function, along with the required arguments. The "query_maker" function is designed to accept human input as an argument and construct the SQL query. Meanwhile, the "run_sql_query" function is responsible for executing the query. Please refrain from independently crafting SQL queries.
Once you receive the results from the Admin in response to the SQL query, ensure that you interpret them accurately. You are also authorized to create SQL queries tailored to user input. Subsequently, execute the query and provide the results. In the event of any errors, please rectify them and rerun the query, and then present the answer.
If the query result is empty, then just say we do not have this data in database.
'''


# openai api key
api_key = ""

# Set your LLms Endpoint
config_list_gpt_turbo = autogen.config_list_from_models(model_list=["gpt-4o-mini"])


def query_maker(user_input):
    # make sql queries using LLM chain
    openaiLLM = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=api_key, cache=False)
    prompt_template = PromptTemplate.from_template("{system_prompt} + '\n' +  {user_input}.")

    chain = LLMChain(llm=openaiLLM, prompt=prompt_template)
    query1 = chain.run({"system_prompt": query_maker_gpt_system_prompt, "user_input": user_input})
    query2 = chain.run({"system_prompt": query_maker_gpt_system_prompt, "user_input": user_input})

    return query1, query2


def run_sql_query(sql_query):
    # Specify the SQLite database file
    db_name = "dishes.db"

    print(sql_query)
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(db_name)

        # Create a cursor to perform database operations
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(sql_query)

        # Fetch all the rows
        result = cursor.fetchall()

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except sqlite3.Error as e:
        print("Error connecting to SQLite database:", e)

    return result

def compare_multiple_query_maker(script: Annotated[str, "Valid Python cell to execute."]):
    return user_proxy.execute_code_blocks([('python', script)])


# another way of registering functions is to use the register_function
def draw_graph(script: Annotated[str, "Valid Python cell to execute."]) -> str:
    return user_proxy.execute_code_blocks([('python', script)])


gpt_turbo_config = {
    "temperature": 0,
    "config_list": config_list_gpt_turbo,
    "functions": [
        {
            "name": "query_maker",
            "description": "generates sql query as per user input",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "This is the input from the user side.",
                    }
                    ,
                },
                "required": ["user_input"],
            },
        },

        {
            "name": "compare_sql_queries",
            "description": "generate python code that compares 2 queries. If the 2 queries are the same, return 1 of the 2 queries. Otherwise, if the 2 queries are different, run the query_maker function again. You can only run it a maximum of 5 times.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "This is input from query_maker function",
                    }
                    ,
                },
                "required": ["script"],
            },
        },

        {
            "name": "run_sql_query",
            "description": "This function is used to run sql query against user input to get the results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "This is the mysql query.",
                    }
                    ,
                },
                "required": ["sql_query"],
            },
        },
    ]
}
function_map = {"query_maker": query_maker,
                "compare_sql_queries": compare_multiple_query_maker,
                "run_sql_query": run_sql_query}

termination_msg = ("If everything looks good, respond with Approved"
                   " or If the result cannot be returned then respond with Approved")


def is_termination_msg(content):
    have_content = content.get("content", None) is not None
    if have_content and "Approved" in content["content"]:
        return True
    else:
        return False


user_proxy = autogen.UserProxyAgent(
    name="Admin",
    system_message=admin_prompt + termination_msg,
    human_input_mode="NEVER",
    is_termination_msg=is_termination_msg,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False
    }

)

engineer = autogen.AssistantAgent(
    name="Assistant Agent",
    llm_config=gpt_turbo_config,
    system_message=assistant_agent_prompt + termination_msg,
    function_map=function_map,
)


user_input = 'đặt cho tôi 2 bát bun ga'

user_proxy.register_function(function_map={"query_maker": query_maker,
                                           "compare_sql_queries": compare_multiple_query_maker,
                                           "run_sql_query": run_sql_query})

user_proxy.initiate_chat(engineer, message=f"{user_input}", clear_history=True)

user_proxy_chat = user_proxy.chat_messages
engineer_chat = engineer.chat_messages
