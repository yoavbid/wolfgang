import os
import time
import streamlit as st
import string
import random
import boto3

os.environ['OPENAI_API_KEY'] = st.secrets["api_secret"]

from utils import ask_question, get_chat_chain_and_store

# params
num_contexts = 8
temperature = 0.4
prompt_path = "prompt.txt"
enable_log = True

def write_log_to_s3(log_data, bucket_name, file_name):
    # Create an S3 client
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws_secret_access_key"])

    # Write the log data to a file
    log_file = '\n'.join(log_data)  # Assuming log_data is a list of strings
    log_file += '\n'  # Add a new line at the end

    # Upload the log file to S3
    s3.put_object(Body=log_file, Bucket=bucket_name, Key=file_name)
    
    
def update_log_on_s3(log_update, bucket_name, file_name):
    # Create an S3 client
    s3 = boto3.client('s3',
                      aws_access_key_id=st.secrets["aws_access_key_id"],
                      aws_secret_access_key=st.secrets["aws_secret_access_key"])

    # Retrieve the existing log file from S3
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    existing_log = response['Body'].read().decode('utf-8')

    # Make the necessary updates to the log
    updated_log = existing_log + '\n'.join(log_data) + '\n'

    # Upload the updated log file back to S3
    s3.put_object(Body=updated_log, Bucket=bucket_name, Key=file_name)


def generate_response(prompt, chat, store, history, recent_level=None):
  message, _ = ask_question(prompt,
                            history,
                            chat,
                            store,
                            recent_level,
                            num_contexts=num_contexts)
  return message


st.set_page_config(layout="wide")
st.title("Wolfgang")
param_col, chat_col = st.columns([1, 3])

with param_col:
  username = st.text_input(
    "Your name",
    key="user_name",
    placeholder="default: anonymous")
  recent_level = st.text_input(
    "Most recently played level and course (free text, set before first question)",
    key="recent_level",
    placeholder="e.g. Essentials 3, Mamma Mia")
  model = st.selectbox("Model (set before first question)",
                       ["gpt-3.5-turbo", "gpt-4"],
                       key="model")

with chat_col:
  if ("generated" not in st.session_state or "past" not in st.session_state
      or "chat" not in st.session_state):
    chat, store = get_chat_chain_and_store(prompt_path,
                                           model,
                                           temperature,
                                           logger=None)

    st.session_state["chat"] = chat
    st.session_state["store"] = store
    st.session_state["history"] = []
    st.session_state["first_input_given"] = False

    st.session_state["generated"] = []
    st.session_state["past"] = []
    

  user_input = st.text_input("Enter your question here", key="input")

  if user_input:
    if not st.session_state["first_input_given"] and enable_log:
      if not username:
        username = "anonymous"
        
      st.session_state["log_filename"] = "%s_%s_%s.txt" % (
        time.strftime("%Y%m%d-%H%M%S"), 
        username,
        ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6)))
      
      log_data = ["Model: %s" % (model, )]
      log_data.append("Recent level: %s" % (recent_level, ))
      write_log_to_s3(log_data, "wolfgang-tutor-logs", st.session_state["log_filename"])
      st.session_state["first_input_given"] = True

    output = generate_response(user_input, st.session_state["chat"],
                               st.session_state["store"],
                               st.session_state["history"], recent_level)

    st.session_state["past"].append(user_input)
    st.session_state["generated"].append(output)

    if enable_log:
      log_data = ["You: " + user_input]
      log_data.append("Wolfgang: " + output)
      update_log_on_s3(log_data, "wolfgang-tutor-logs", st.session_state["log_filename"])

  if st.session_state["generated"]:
    for i in range(len(st.session_state["generated"])):
      st.write("You: " + st.session_state["past"][i])
      st.write("Wolfgang: " + st.session_state["generated"][i])

if enable_log and "log_filename" in st.session_state:
  with param_col:
    st.markdown("Your log filename: %s" % (st.session_state["log_filename"], ))
