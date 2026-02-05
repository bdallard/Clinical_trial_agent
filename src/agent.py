"""Clinical trials agent with function calling"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

try:
    from .clinical_trials_api import (
        count_trials,
        show_trials,
        search_trials,
        analyze_criteria,
        calculate_statistics,
        extract_sites,
    )
    from .models import FeasibilityResponse
    from .logger import ConversationLogger, print_tool_call
except ImportError:
    from clinical_trials_api import (
        count_trials,
        show_trials,
        search_trials,
        analyze_criteria,
        calculate_statistics,
        extract_sites,
    )
    from models import FeasibilityResponse
    from logger import ConversationLogger, print_tool_call

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "count_trials",
            "description": "Count the NUMBER OF TRIALS matching criteria. Use ONLY for 'how many trials exist' questions. Does NOT return patient/enrollment numbers or trial details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Medical condition"},
                    "phase": {"type": "string", "description": "Trial phase"},
                    "status": {"type": "string", "description": "Trial status (e.g., 'Recruiting')"},
                    "location": {"type": "string", "description": "Country or city"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_trials",
            "description": "Show full details for a specific trial by NCT ID. Use when user asks about a specific trial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nctId": {"type": "string", "description": "NCT ID (e.g., 'NCT03264352')"}
                },
                "required": ["nctId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_trials",
            "description": "Search for trials and get details including: title, phase, status, sponsor, ENROLLMENT/PATIENT COUNTS, dates, eligibility, locations. Use this for questions about patient numbers, enrollment sizes, or listing trials.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Medical condition (e.g., 'diabetes', 'asthma')"},
                    "phase": {"type": "string", "description": "Trial phase (e.g., 'Phase 1', 'Phase 2', 'Phase 3')"},
                    "status": {"type": "string", "description": "Trial status (e.g., 'Recruiting', 'Completed'). Omit this parameter to get all trials regardless of status."},
                    "location": {"type": "string", "description": "Country name (e.g., 'France', 'United States')"},
                    "sponsor": {"type": "string", "description": "Lead sponsor name (e.g., 'Pfizer', 'Novartis')"},
                    "intervention": {"type": "string", "description": "Intervention/treatment name (e.g., 'insulin')"},
                    "study_type": {"type": "string", "description": "Study type: 'Interventional' or 'Observational'"},
                    "start_date_from": {"type": "string", "description": "Filter trials starting after this date (YYYY-MM-DD)"},
                    "start_date_to": {"type": "string", "description": "Filter trials starting before this date (YYYY-MM-DD)"},
                    "max_results": {"type": "integer", "description": "Maximum results (default: 10, max: 20)", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_criteria",
            "description": "Extract and analyze eligibility criteria patterns (inclusion/exclusion) from trial data. Use after search_trials.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trials": {"type": "string", "description": "JSON string of trial data from search_trials"}
                },
                "required": ["trials"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_statistics",
            "description": "Calculate statistics from trials: phase distribution, status counts, sponsor breakdown, AVERAGE ENROLLMENT/PATIENT NUMBERS, and AVERAGE TRIAL DURATION (in days/months/years). Makes its own API call. Use for questions about patient numbers, trial duration, or summary statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Medical condition (e.g., 'diabetes', 'type 2 diabetes')"},
                    "phase": {"type": "string", "description": "Trial phase (e.g., 'Phase 3')"},
                    "status": {"type": "string", "description": "Trial status (e.g., 'Completed'). Omit for all statuses."},
                    "location": {"type": "string", "description": "Country name (e.g., 'France')"},
                    "sponsor": {"type": "string", "description": "Lead sponsor name"},
                    "max_results": {"type": "integer", "description": "Max trials to analyze (default: 20)", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_sites",
            "description": "Extract site/facility information from trials. Makes its own API call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Medical condition"},
                    "phase": {"type": "string", "description": "Trial phase"},
                    "status": {"type": "string", "description": "Trial status"},
                    "location": {"type": "string", "description": "Filter by country/city"},
                    "max_results": {"type": "integer", "description": "Max trials to check (default: 10, max: 20)", "default": 10}
                }
            }
        }
    }
]

# Function mapping
AVAILABLE_FUNCTIONS = {
    "count_trials": count_trials,
    "search_trials": search_trials,
    "show_trials": show_trials,
    "analyze_criteria": analyze_criteria,
    "calculate_statistics": calculate_statistics,
    "extract_sites": extract_sites
}


SYSTEM_PROMPT = """You are a helpful clinical trial feasibility assistant. You help pharma companies plan trials by querying ClinicalTrials.gov and providing insights about trials, eligibility criteria, patient counts, and sites.

RESPONSE STRUCTURE:
- 'answer': Brief summary/intro text (e.g., "Found 5 Phase 3 diabetes trials in France")
- 'trials': Populate with trial details when listing trials (nct_id, title, phase, status, sponsor, enrollment, dates)
- 'sites': Populate with site details when listing facilities (nct_id, facility, city, country)
- 'criteria': Populate with inclusion/exclusion lists when asked about eligibility criteria
- 'sources': Always include NCT IDs of trials referenced

RULES:
1. Use structured fields (trials, sites, criteria) instead of putting details in the answer text
2. The 'answer' field should be a brief intro, not repeat what's in structured fields
3. Always populate 'sources' with NCT IDs
4. Include ALL items from tool results - never give incomplete data"""


class Agent:
    """Clinical trials agent with conversation memory"""
    
    def __init__(self, model: str = "gpt-4o-mini", logger: ConversationLogger | None = None):
        self.model = model
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.logger = logger
    
    def clear_memory(self):
        """Reset conversation history"""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.logger:
            self.logger.log_memory_cleared()
    
    def run(self, user_question: str) -> FeasibilityResponse:
        """Process a question with memory of previous messages"""
        print(f"\n🤔 Question: {user_question}\n")
        
        # Log user message
        if self.logger:
            self.logger.log_user_message(user_question)
        
        # Add user message to memory
        self.messages.append({"role": "user", "content": user_question})
        
        # First LLM call with tools
        response = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # If no tool calls, return answer
        if not tool_calls:
            self.messages.append(response_message)
            if self.logger:
                self.logger.log_assistant_response(response_message.content)
            return response_message.content
        
        # Execute tool calls
        self.messages.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Pretty print tool call to console
            print_tool_call(function_name, function_args)
            
            function_to_call = AVAILABLE_FUNCTIONS[function_name]
            
            # Handle trials parameter (passed as JSON string) for analyze_criteria
            if "trials" in function_args and function_name == "analyze_criteria":
                function_args["trials"] = json.loads(function_args["trials"])
            
            function_response = function_to_call(**function_args)
            
            # Log tool call with parameters and result
            if self.logger:
                self.logger.log_tool_call(function_name, function_args, function_response)
            
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response)
            })
        
        # Second LLM call with structured output
        final_response = client.beta.chat.completions.parse(
            model=self.model,
            messages=self.messages,
            response_format=FeasibilityResponse
        )
        
        result = final_response.choices[0].message.parsed
        
        # Store assistant response in memory
        self.messages.append({"role": "assistant", "content": result.answer})
        
        # Log assistant response
        if self.logger:
            self.logger.log_assistant_response(result)
        
        return result


# Convenience function for backward compatibility
def run_agent(user_question: str, model: str = "gpt-4o-mini") -> FeasibilityResponse:
    """Stateless version (no memory between calls)"""
    agent = Agent(model=model)
    return agent.run(user_question)
