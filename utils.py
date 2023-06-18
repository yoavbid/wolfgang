import logging
import time
import faiss
import pickle
from langchain import LLMChain
import pickle
from langchain.prompts import Prompt
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
  ChatPromptTemplate,
  SystemMessagePromptTemplate,
)


def get_chat_chain_and_store(prompt_path,
                             model='gpt-3.5-turbo',
                             temperature=0.4,
                             logger=None):
  if logger is None:
    logger = get_default_logger()

  store = get_index_store()

  with open(prompt_path, "r") as f:
    promptTemplate = f.read()

    system_message_prompt = SystemMessagePromptTemplate.from_template(
      template=promptTemplate,
      input_variables=["history", "context", "recent_level", "input"])

  chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

  chat = ChatOpenAI(temperature=temperature, model=model)

  chain = LLMChain(llm=chat, prompt=chat_prompt)

  return chain, store


def ask_question(question,
                 history,
                 chain,
                 store,
                 recent_level=None,
                 num_contexts=8):
  search_text = question
  if recent_level is not None:
    search_text += ' context: ' + recent_level

  docs = store.similarity_search(search_text, k=num_contexts)
  contexts = []
  contexts_no_index = []
  for i, doc in enumerate(docs):
    contexts.append(f"Context {i}:\n{doc.page_content}")
    contexts_no_index.append(doc.page_content)

  answer = chain.run(input=question,
                     context="\n\n".join(contexts),
                     recent_level=recent_level,
                     history=history)

  history.append(f"Human: {question}")
  history.append(f"Bot: {answer}")

  return answer, contexts_no_index


def get_index_store():
  index = faiss.read_index("app_context.index")

  with open("faiss.pkl", "rb") as f:
    store = pickle.load(f)

  store.index = index

  return store


def setup_logger(name):
  logger = logging.getLogger()
  logger.level = logging.INFO
  logger.addHandler(logging.StreamHandler())
  time_str = time.strftime("%Y%m%d-%H%M%S")
  logger.addHandler(
    logging.FileHandler(simply_tutor_path / ("logs/%s_%s.txt" %
                                             (name, time_str)),
                        mode="w"))

  return logger, time_str


def get_default_logger():
  logger = logging.getLogger()
  logger.level = logging.INFO
  logger.addHandler(logging.StreamHandler())

  return logger
