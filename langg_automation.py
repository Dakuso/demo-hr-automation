import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv() 
api_key = os.getenv("ANTHROPIC_API_KEY")
model = ChatAnthropic(model="claude-3-opus-20240229", api_key=api_key)

class State(TypedDict):
    input: str
    recClassification: bool
    output: str

class RequestClassification(BaseModel):
    """ Classifies the requests into change requests and others """
    classification: bool = Field(description="True if the Mail mentions changes in employee core data, False otherwise")

classificator = model.with_structured_output(RequestClassification)

def request_classifier(state: State):
    request = state['input']
    decision = classificator.invoke([
        SystemMessage(content="Based on the following input, please evaluate whether a person is trying to change some employee core data or not"),
        HumanMessage(content=f"Here is the Input in question: \n {request}"),
    ])

    print('############################ ', decision)
    return {'recClassification': decision.classification}


def request_router(state: State):
    if state['recClassification'] in (False, True):
        return state['recClassification']
    else:
        raise ValueError("Invalid decision value")


def request_processor(state: State):
    return {'output': 'very successful run'}

builder = StateGraph(State)
builder.add_node("change_request", request_classifier)
builder.add_node("request_processing", request_processor)
builder.add_edge(START, "change_request")
builder.add_conditional_edges(
    "change_request",
    request_router,
    {
        1: 'request_processing',
        0: END,
    }
)
builder.add_edge("request_processing", END)
workflow = builder.compile()


# Wrap the execution logic in a main function
def main():
    """Main function to run the LangGraph workflow."""
    message = "if you could please change leon's number to 0791234567"
    # message = "ahdhdfbgeda"
    state = workflow.invoke({"input": message})
    print(state)

# Standard entry point to run the script
if __name__ == "__main__":
    main()