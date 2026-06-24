### This is purely meant to be pseudo code that may not even run.

from typing import Annotated
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_mesages
from langgraph.checkpoint.memory import InMemorySaver # for saving memory
from langchain_ollama import ChatOllama # For using llms
from colorama import Fore

# Create LLM
llm = ChatOllama(model='qwen2.5:14b')

# 3. Create State
class State(dict):
    messages: Annotated[list, add_messages] # every time a new state