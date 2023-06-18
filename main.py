import os
import time
import streamlit as st

os.environ['OPENAI_API_KEY'] = st.secrets["api_secret"]

from utils import ask_question, get_chat_chain_and_store

# params
num_contexts = 8
temperature = 0.4
prompt_path = "prompt.txt"


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
  recent_level = st.text_input(
    "Most recently played level and course (free text, set before first question)",
    key="recent_level")
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
    
    if not os.path.exists("logs"):
      os.mkdir("logs")

    st.session_state["log_filename"] = "logs/%s.txt" % (
      time.strftime("%Y%m%d-%H%M%S"), )

  user_input = st.text_input("Enter your question here", key="input")

  if user_input:
    if not st.session_state["first_input_given"]:
      with open(st.session_state["log_filename"], 'w') as f:
        f.write("Model: %s\n" % (model, ))
        f.write("Recent level: %s\n" % (recent_level, ))
      st.session_state["first_input_given"] = True

    output = generate_response(user_input, st.session_state["chat"],
                               st.session_state["store"],
                               st.session_state["history"], recent_level)

    st.session_state["past"].append(user_input)
    st.session_state["generated"].append(output)

    with open(st.session_state["log_filename"], "a") as f:
      f.write("You: " + user_input + "\n")
      f.write("Wolfgang: " + output + "\n")

  if st.session_state["generated"]:
    for i in range(len(st.session_state["generated"])):
      st.write("You: " + st.session_state["past"][i])
      st.write("Wolfgang: " + st.session_state["generated"][i])

with param_col:
  st.markdown("Your log filename: %s" % (st.session_state["log_filename"], ))
