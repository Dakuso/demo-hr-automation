import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

class State(TypedDict):
    input: str
    recClassification: bool
    output: str
    currentData: str
    proposedData: str
    error: str

class RequestClassification(BaseModel):
    """ Classifies the requests into change requests and others """
    classification: bool = Field(description="True if the Mail mentions changes in employee core data, False otherwise")

def create_workflow(api_key: str = None):
    """Create and return the workflow with the specified API key."""
    
    # Use provided API key or fall back to environment variable
    if api_key is None:
        load_dotenv() 
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("API key must be provided either as parameter or ANTHROPIC_API_KEY environment variable")
    
    model = ChatAnthropic(model="claude-3-opus-20240229", api_key=api_key)
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
        """ Function is a bit loaded, TODO: Separate properly """
        request = state['input']
        output = model.invoke([
            SystemMessage(content="""
Hello there. I would like you to be part of my process. 
Essentially you will be going through messages and parse out the personal Information that should be adapted Change. Your Options for personal Information are as follows:

FirstName, LastName, DateOfBirth, AHV_Number, Nationality, SwissCitizen, WorkPermit, MaritalStatus, StreetAddress, PostalCode, City, Canton, PhoneNumber, PersonalEmail, JobTitle, Department, HireDate, WorkloadPercentage, AnnualGrossSalary_CHF, IBAN, BankName, TaxAtSource_Code

Please only parse the new Information and ignore anything else. I expect Output in json Format: i want you to provide me with all the Information that you parsed such as:

{'LastName': 'Meier', 'MaritalStatus': 'Married', 'WorkloadPercentage': 80}

Always include the name of the Person so we know who we talk about and if you could only respond with valid json please!
"""),
            HumanMessage(content=f"Here is the message i would like you to parse: \n {request}"),
        ])
        
        # Extracting JSON changes
        try:
            changes = json.loads(output.content)
        except:
            raise ValueError(f"There was no valid JSON parsed \n\n {output.content}")
        
        # Loading Database at runtime TODO: 
        try:
            DATA_FILENAME = Path(__file__).parent/'data/employee_data.csv'
            raw_gdp_df = pd.read_csv(DATA_FILENAME)
        
        except FileNotFoundError:
            # Return an empty DataFrame if the file is not found
            raw_gdp_df = pd.DataFrame()
        
        # Locate Person 
        matching_entry = raw_gdp_df[
        (raw_gdp_df['FirstName'] == changes['FirstName']) &
        (raw_gdp_df['LastName'] == changes['LastName'])
        ]

        # Generate Changes
        if matching_entry.shape[0] == 0:
            raise ValueError(f"No employee found for {changes['FirstName']} {changes['LastName']}.")
        elif matching_entry.shape[0] == 1:
            new_values = matching_entry.copy()
            pass
        else:
            raise ValueError(f"Found more than one employee for {changes['FirstName']} {changes['LastName']}.")
        
        for column, new_value in changes.items():
            new_values[column] = new_value

        return {'output': output.content, 'currentData': matching_entry, 'proposedData': new_values}

    # Build the workflow
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
    
    return builder.compile()

def process_employee_request(message: str, api_key: str = None):
    """
    Process an employee data change request.
    
    Args:
        message (str): The request message to process
        api_key (str, optional): Anthropic API key. If None, will use ANTHROPIC_API_KEY env var
    
    Returns:
        dict: The workflow state result
    """
    workflow = create_workflow(api_key)
    return workflow.invoke({"input": message})

def main():
    """Main function to run the LangGraph workflow."""
    message = "if you could please change anna's number to 0791234567, Müller that is also switch iban to CH560023323312345678B"
    # message = "ahdhdfbgeda"
    state = process_employee_request(message)
    return state

# Standard entry point to run the script
if __name__ == "__main__":
    state = main()
    print(state)