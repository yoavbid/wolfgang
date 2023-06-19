import os
import time
import streamlit as st
import string
import random
import boto3
import openai.error
import openai

from utils import ask_question, get_chat_chain_and_store

# params
NUM_CONTEXTS = 8
TEMPERATURE = 0.4
PROMPT_PATH = "prompt.txt"
LOG_ENABLED = True
LOG_S3_BUCKET = "wolfgang-tutor-logs"

def write_log_to_s3(log_data, file_name):
    # Create an S3 client
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws_secret_access_key"])

    # Write the log data to a file
    log_file = '\n'.join(log_data)  # Assuming log_data is a list of strings
    log_file += '\n'  # Add a new line at the end

    # Upload the log file to S3
    s3.put_object(Body=log_file, Bucket=LOG_S3_BUCKET, Key=file_name)
    
    
def update_log_on_s3(log_data, file_name):
    # Create an S3 client
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws_secret_access_key"])

    # Retrieve the existing log file from S3
    response = s3.get_object(Bucket=LOG_S3_BUCKET, Key=file_name)
    existing_log = response['Body'].read().decode('utf-8')

    # Make the necessary updates to the log
    updated_log = existing_log + '\n'.join(log_data) + '\n'

    # Upload the updated log file back to S3
    s3.put_object(Body=updated_log, Bucket=LOG_S3_BUCKET, Key=file_name)
    
def create_log(model, recent_level, username):
  if not username:
    username = "anonymous"
    
  st.session_state["log_filename"] = "%s_%s_%s.txt" % (
    time.strftime("%Y%m%d-%H%M%S"), 
    username,
    ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
  
  log_data = ["Model: %s" % (model, )]
  log_data.append("Recent level: %s" % (recent_level, ))
  write_log_to_s3(log_data, st.session_state["log_filename"])


def generate_response(prompt, chat, store, history, recent_level=None):
  try:
    message, _ = ask_question(prompt,
                              history,
                              chat,
                              store,
                              recent_level,
                              num_contexts=NUM_CONTEXTS)
  except openai.error.InvalidRequestError as e:
    update_log_on_s3(["Encountered OpenAI error: ", str(e)], st.session_state["log_filename"])
    message = "Sorry. Failed to communicate with my brain. Please start a new session and try again."
    
  return message


def submit_question():
    st.session_state.question = st.session_state.input
    st.session_state.input = ''
    
    
def show_params():
  username = st.text_input(
    "Your name",
    key="user_name",
    placeholder="default: anonymous")
  recent_level = st.text_input(
    "Most recently played level and course (free text, set before first question)",
    key="recent_level",
    placeholder="e.g. Essentials 3, Mamma Mia")
  model = st.selectbox("Model (set before first question)",
                      ["gpt-4", "gpt-3.5-turbo"],
                      key="model")
  
  return username, recent_level, model

def initialize_chat(model):
  chat, store = get_chat_chain_and_store(PROMPT_PATH,
                                        model,
                                        TEMPERATURE,
                                        logger=None)
  st.session_state["chat"] = chat
  st.session_state["store"] = store
  st.session_state["history"] = []
  st.session_state["first_input_given"] = False
  st.session_state["generated"] = []
  st.session_state["past"] = []
  

def show_chat(username, recent_level, model):
  if ("generated" not in st.session_state or "past" not in st.session_state
        or "chat" not in st.session_state):
    initialize_chat(model)
      
  st.text_input("Enter your question here", key="input", on_change=submit_question)

  if st.session_state["question"]:
    if not st.session_state["first_input_given"] and LOG_ENABLED:
      create_log(model, recent_level, username)
      st.session_state["first_input_given"] = True

    output = generate_response(st.session_state["question"], st.session_state["chat"],
                              st.session_state["store"],
                              st.session_state["history"], recent_level)

    st.session_state["past"].append(st.session_state["question"])
    st.session_state["generated"].append(output)

    if LOG_ENABLED:
      log_data = ["You: " + st.session_state["question"]]
      log_data.append("Wolfgang: " + output)
      update_log_on_s3(log_data, st.session_state["log_filename"])

  if st.session_state["generated"]:
    for i in range(len(st.session_state["generated"])):
      st.write("You: " + st.session_state["past"][i])
      st.write("Wolfgang: " + st.session_state["generated"][i])


def main():
  # set API key in two ways to support both local and remote execution
  os.environ['OPENAI_API_KEY'] = st.secrets["api_secret"]
  openai.api_key = st.secrets["api_secret"]
  
  st.set_page_config(layout="wide")
  st.title("WolfgangGPT beta")
  param_col, chat_col = st.columns([1, 3])

  if 'question' not in st.session_state:
    st.session_state["question"] = '' 

  with param_col:
    username, recent_level, model = show_params()

  with chat_col:
    show_chat(username, recent_level, model)
    
  with param_col:
    if LOG_ENABLED and "log_filename" in st.session_state:
      st.markdown("Your log filename: %s" % (st.session_state["log_filename"], ))


if __name__ == "__main__":
  main()