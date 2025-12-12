import streamlit as st
import pandas as pd
import json
from openai import OpenAI

# ---------- App config ----------
st.set_page_config(
    page_title="NHS Pension Planner",
    page_icon="💼",
    layout="wide"
)

# ---------- NHSBSA Design Standards ----------
# NHS Identity colours: https://www.england.nhs.uk/nhsidentity/identity-guidelines/colours/

NHS_BLUE = "#005EB8"
NHS_DARK_BLUE = "#003087"
NHS_BRIGHT_BLUE = "#0072CE"
NHS_LIGHT_BLUE = "#41B6E6"
NHS_AQUA_BLUE = "#00A9CE"
NHS_BLACK = "#231f20"
NHS_DARK_GREY = "#425563"
NHS_MID_GREY = "#768692"
NHS_PALE_GREY = "#E8EDEE"
NHS_GREEN = "#009639"
NHS_DARK_GREEN = "#006747"
NHS_LIGHT_GREEN = "#78BE20"
NHS_AQUA_GREEN = "#00A499"
NHS_YELLOW = "#FAE100"
NHS_WARM_YELLOW = "#FFB81C"

# Custom CSS for NHS styling
st.markdown(f"""
    <style>
        /* Main header styling */
        .stApp header {{
            background-color: {NHS_BLUE};
        }}
        
        /* Title styling */
        h1 {{
            color: {NHS_BLUE} !important;
        }}
        
        h2, h3 {{
            color: {NHS_DARK_BLUE} !important;
        }}
        
        /* Primary button styling */
        .stButton > button {{
            background-color: {NHS_GREEN} !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
        }}
        
        .stButton > button:hover {{
            background-color: {NHS_DARK_GREEN} !important;
        }}
        
        /* Form submit button */
        .stFormSubmitButton > button {{
            background-color: {NHS_GREEN} !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            font-weight: 600 !important;
            width: 100%;
        }}
        
        .stFormSubmitButton > button:hover {{
            background-color: {NHS_DARK_GREEN} !important;
        }}
        
        /* Metric styling */
        [data-testid="stMetricValue"] {{
            color: {NHS_BLUE} !important;
            font-weight: bold !important;
        }}
        
        /* Info box styling */
        .stAlert {{
            border-left-color: {NHS_BLUE} !important;
        }}
        
        /* Link styling */
        a {{
            color: {NHS_BLUE} !important;
        }}
        
        a:hover {{
            color: {NHS_DARK_BLUE} !important;
        }}
        
        /* Expander styling */
        .streamlit-expanderHeader {{
            color: {NHS_DARK_BLUE} !important;
            font-weight: 600 !important;
        }}
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {NHS_PALE_GREY} !important;
        }}
        
        /* Footer link cards */
        .nhs-link-card {{
            background-color: {NHS_PALE_GREY};
            border-left: 4px solid {NHS_BLUE};
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .nhs-link-card h4 {{
            color: {NHS_DARK_BLUE} !important;
            margin: 0 0 8px 0;
        }}
        
        .nhs-link-card p {{
            color: {NHS_DARK_GREY};
            margin: 0;
            font-size: 0.9em;
        }}
        
        /* NHS Banner */
        .nhs-banner {{
            background-color: {NHS_BLUE};
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        
        .nhs-banner img {{
            height: 40px;
        }}
        
        /* Warning/disclaimer box */
        .nhs-warning {{
            background-color: {NHS_WARM_YELLOW};
            border-left: 4px solid #ED8B00;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        
        /* Chat container styling */
        .chat-container {{
            background-color: {NHS_PALE_GREY};
            border-radius: 8px;
            padding: 15px;
            height: 100%;
        }}
        
        /* Update notification */
        .update-notification {{
            background-color: {NHS_LIGHT_GREEN};
            color: {NHS_BLACK};
            padding: 10px 15px;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 4px solid {NHS_GREEN};
        }}
    </style>
""", unsafe_allow_html=True)

# ---------- Initialize Session State for Calculator Values ----------
def init_session_state():
    """Initialize all calculator values in session state."""
    defaults = {
        "current_salary": None,  # Required - no default
        "years_of_service": None,  # Required - no default
        "scheme": None,  # Required - no default
        "current_age": None,  # Required - no default
        "retirement_age": None,  # Required - no default
        "normal_pension_age": None,  # Set based on scheme
        "early_reduction_per_year": 4.0,
        "late_increase_per_year": 3.0,
        "commutation_proportion": 15,
        "commutation_factor": 12.0,
        "care_salary_pct": 80,
        "salary_growth_rate": 2.0,  # Annual salary growth %
        "investment_growth_rate": 4.0,  # Expected investment growth %
        "inflation_rate": 2.5,  # Inflation assumption %
        "messages": [],
        "api_key": "",
        "calculator_updated": False,
        "update_message": "",
        "pending_updates": {},  # Store updates to apply before widgets render
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def apply_pending_updates():
    """Apply any pending updates before widgets are rendered."""
    if st.session_state.pending_updates:
        for key, value in st.session_state.pending_updates.items():
            st.session_state[key] = value
        st.session_state.pending_updates = {}

init_session_state()
apply_pending_updates()  # Apply any pending updates from AI before widgets render

# ---------- Helper functions ----------

def get_missing_required_fields() -> list:
    """Check which required fields are still missing."""
    required_fields = {
        "current_salary": "current salary",
        "current_age": "current age",
        "years_of_service": "years of NHS service",
        "scheme": "pension scheme",
        "retirement_age": "planned retirement age"
    }
    missing = []
    for field, label in required_fields.items():
        if st.session_state.get(field) is None:
            missing.append(label)
    return missing

def has_required_fields() -> bool:
    """Check if all required fields are set."""
    return len(get_missing_required_fields()) == 0

def nhs_scheme_parameters(scheme: str):
    """
    Returns accrual_rate, automatic_lump_factor, default_normal_pension_age, description
    """
    if scheme == "1995 Section (final salary)":
        return 1 / 80, 3.0, 60, "Final salary, 1/80th pension plus 3x automatic lump sum."
    elif scheme == "2008 Section (final salary)":
        return 1 / 60, 0.0, 65, "Final salary, 1/60th pension, no automatic lump sum."
    else:  # 2015 Scheme (CARE)
        return 1 / 54, 0.0, 67, "Career average (CARE), 1/54th of pensionable earnings each year."


def calculate_nhs_pension(
    scheme: str,
    current_salary: float,
    years_of_service: float,
    retirement_age: int,
    normal_pension_age: int,
    early_reduction_per_year: float,
    late_increase_per_year: float,
    commutation_proportion: float,
    commutation_factor: float,
    care_salary_pct: float,
    current_age: int = 45,
    salary_growth_rate: float = 0.02,
    inflation_rate: float = 0.025,
):
    """Calculate NHS pension for a single section."""
    accrual_rate, automatic_lump_factor, _, _ = nhs_scheme_parameters(scheme)

    # Calculate years until retirement and projected salary
    years_to_retirement = max(0, retirement_age - current_age)
    projected_salary = current_salary * ((1 + salary_growth_rate) ** years_to_retirement)
    
    if scheme in ["1995 Section (final salary)", "2008 Section (final salary)"]:
        # Final salary schemes use projected salary at retirement
        pensionable_pay = projected_salary
    else:
        # CARE scheme: estimate career average with salary growth
        # Average salary over career considering growth
        if salary_growth_rate > 0 and years_of_service > 0:
            # Calculate average salary over the service period with growth
            # This approximates the career average by taking the midpoint salary
            years_already_worked = years_of_service - years_to_retirement
            if years_already_worked < 0:
                years_already_worked = 0
            
            # Estimate average: use geometric mean approximation
            start_salary = current_salary / ((1 + salary_growth_rate) ** years_already_worked) if years_already_worked > 0 else current_salary
            end_salary = projected_salary
            
            # Career average is roughly the salary at the midpoint of service
            mid_years = years_of_service / 2
            avg_salary = current_salary * ((1 + salary_growth_rate) ** (years_to_retirement - (years_of_service - mid_years)))
            pensionable_pay = avg_salary * (care_salary_pct / 100.0)
        else:
            pensionable_pay = current_salary * (care_salary_pct / 100.0)

    base_annual_pension = pensionable_pay * accrual_rate * years_of_service

    years_diff = retirement_age - normal_pension_age
    if years_diff < 0:
        factor = (1 - early_reduction_per_year) ** abs(years_diff)
    elif years_diff > 0:
        factor = (1 + late_increase_per_year) ** abs(years_diff)
    else:
        factor = 1.0

    adjusted_annual_pension = base_annual_pension * factor
    automatic_lump_sum = adjusted_annual_pension * automatic_lump_factor
    commuted_annual_pension = adjusted_annual_pension * commutation_proportion
    extra_commutation_lump_sum = commuted_annual_pension * commutation_factor
    annual_pension_after_commutation = adjusted_annual_pension - commuted_annual_pension
    total_lump_sum = automatic_lump_sum + extra_commutation_lump_sum
    
    # Calculate real-terms values (adjusted for inflation)
    # This shows what the pension is worth in today's money
    inflation_factor = (1 + inflation_rate) ** years_to_retirement
    real_annual_pension = annual_pension_after_commutation / inflation_factor if inflation_factor > 0 else annual_pension_after_commutation
    real_lump_sum = total_lump_sum / inflation_factor if inflation_factor > 0 else total_lump_sum

    return {
        "pensionable_pay": pensionable_pay,
        "projected_salary": projected_salary,
        "accrual_rate": accrual_rate,
        "automatic_lump_factor": automatic_lump_factor,
        "base_annual_pension": base_annual_pension,
        "early_late_adjustment_factor": factor,
        "adjusted_annual_pension": adjusted_annual_pension,
        "commuted_annual_pension": commuted_annual_pension,
        "annual_pension_after_commutation": annual_pension_after_commutation,
        "automatic_lump_sum": automatic_lump_sum,
        "extra_commutation_lump_sum": extra_commutation_lump_sum,
        "total_lump_sum": total_lump_sum,
        "real_annual_pension": real_annual_pension,
        "real_lump_sum": real_lump_sum,
        "years_to_retirement": years_to_retirement,
    }


# ---------- OpenAI Function Calling for Calculator Updates ----------

CALCULATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_calculator",
            "description": "Update the pension calculator with new values. Use this when the user asks to change calculator settings, run scenarios, or explore different options. Always provide a helpful explanation of what changed and why.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_salary": {
                        "type": "number",
                        "description": "Annual pensionable pay in GBP (e.g., 45000)"
                    },
                    "years_of_service": {
                        "type": "number",
                        "description": "Total years of NHS pensionable service (0-50)"
                    },
                    "scheme": {
                        "type": "string",
                        "enum": ["1995 Section (final salary)", "2008 Section (final salary)", "2015 Scheme (career average)"],
                        "description": "The NHS pension scheme section"
                    },
                    "current_age": {
                        "type": "integer",
                        "description": "Current age in years (18-75)"
                    },
                    "retirement_age": {
                        "type": "integer",
                        "description": "Planned retirement age (55-75)"
                    },
                    "normal_pension_age": {
                        "type": "integer",
                        "description": "Normal pension age for the scheme (55-75). Typical: 1995=60, 2008=65, 2015=67"
                    },
                    "early_reduction_per_year": {
                        "type": "number",
                        "description": "Early retirement reduction percentage per year (0-10)"
                    },
                    "late_increase_per_year": {
                        "type": "number",
                        "description": "Late retirement increase percentage per year (0-10)"
                    },
                    "commutation_proportion": {
                        "type": "integer",
                        "description": "Percentage of pension to exchange for lump sum (0-30)"
                    },
                    "commutation_factor": {
                        "type": "number",
                        "description": "Lump sum received per £1 of pension given up (8-20)"
                    },
                    "care_salary_pct": {
                        "type": "integer",
                        "description": "For 2015 CARE scheme: career average earnings as % of current pay (50-110)"
                    },
                    "salary_growth_rate": {
                        "type": "number",
                        "description": "Expected annual salary growth percentage (0-10)"
                    },
                    "investment_growth_rate": {
                        "type": "number",
                        "description": "Expected investment/pot growth percentage (0-10)"
                    },
                    "inflation_rate": {
                        "type": "number",
                        "description": "Assumed inflation rate percentage (0-10)"
                    }
                },
                "required": []
            }
        }
    }
]


def process_calculator_update(function_args: dict) -> str:
    """Process the function call and store updates for next rerun.
    Only updates fields that are explicitly provided and have different values."""
    updates = []
    
    field_labels = {
        "current_salary": "Current salary",
        "years_of_service": "Years of service",
        "scheme": "Pension scheme",
        "current_age": "Current age",
        "retirement_age": "Retirement age",
        "normal_pension_age": "Normal pension age",
        "early_reduction_per_year": "Early reduction %",
        "late_increase_per_year": "Late increase %",
        "commutation_proportion": "Commutation %",
        "commutation_factor": "Commutation factor",
        "care_salary_pct": "CARE salary %",
        "salary_growth_rate": "Salary growth %",
        "investment_growth_rate": "Investment growth %",
        "inflation_rate": "Inflation rate %"
    }
    
    for key, value in function_args.items():
        if key in field_labels and value is not None:
            old_value = st.session_state.get(key)
            
            # Only update if value is actually different
            if old_value != value:
                # Store update to be applied on next rerun (before widgets render)
                st.session_state.pending_updates[key] = value
                
                # Format the update message
                if key == "current_salary":
                    updates.append(f"• {field_labels[key]}: £{old_value:,.0f} → £{value:,.0f}")
                elif key in ["early_reduction_per_year", "late_increase_per_year", "salary_growth_rate", "investment_growth_rate", "inflation_rate"]:
                    updates.append(f"• {field_labels[key]}: {old_value}% → {value}%")
                elif key in ["commutation_proportion", "care_salary_pct"]:
                    updates.append(f"• {field_labels[key]}: {old_value}% → {value}%")
                else:
                    updates.append(f"• {field_labels[key]}: {old_value} → {value}")
    
    if updates:
        st.session_state.calculator_updated = True
        st.session_state.update_message = "\n".join(updates)
        return f"Calculator updated:\n" + "\n".join(updates)
    return "No changes made to the calculator."


def get_system_prompt() -> str:
    """Build the system prompt with current calculator state."""
    missing_fields = get_missing_required_fields()
    
    # Build state description
    def format_value(value, prefix="", suffix=""):
        if value is None:
            return "NOT SET"
        return f"{prefix}{value}{suffix}"
    
    def format_currency(value):
        if value is None:
            return "NOT SET"
        return f"£{value:,.0f}"
    
    # Calculate results only if we have all required fields
    if has_required_fields():
        results = calculate_nhs_pension(
            scheme=st.session_state.scheme,
            current_salary=st.session_state.current_salary,
            years_of_service=st.session_state.years_of_service,
            retirement_age=st.session_state.retirement_age,
            normal_pension_age=st.session_state.normal_pension_age or 67,
            early_reduction_per_year=st.session_state.early_reduction_per_year / 100,
            late_increase_per_year=st.session_state.late_increase_per_year / 100,
            commutation_proportion=st.session_state.commutation_proportion / 100,
            commutation_factor=st.session_state.commutation_factor,
            care_salary_pct=st.session_state.care_salary_pct,
            current_age=st.session_state.current_age,
            salary_growth_rate=st.session_state.salary_growth_rate / 100,
            inflation_rate=st.session_state.inflation_rate / 100,
        )
        results_section = f"""CURRENT CALCULATION RESULTS:
- Annual pension (after commutation): £{results['annual_pension_after_commutation']:,.2f}
- Total lump sum: £{results['total_lump_sum']:,.2f}
- Real-terms annual pension: £{results['real_annual_pension']:,.2f}
- Monthly pension: £{results['annual_pension_after_commutation']/12:,.2f}
- Base annual pension: £{results['base_annual_pension']:,.2f}
- Early/late adjustment factor: {results['early_late_adjustment_factor']:.4f}"""
    else:
        results_section = f"""CALCULATION NOT YET POSSIBLE
Missing required information: {', '.join(missing_fields)}
You MUST gather these before providing any pension estimate."""
    
    missing_info = ""
    if missing_fields:
        missing_info = f"""\n\n**IMPORTANT - MISSING REQUIRED INFORMATION:**
The following required fields have NOT been provided yet: {', '.join(missing_fields)}

You MUST ask the user for this information before you can calculate their pension.
Do NOT make up or assume values. Ask for the missing information conversationally.
"""
    
    return f"""You are a friendly NHS pension advisor assistant. Your role is to help users understand their NHS pension through natural conversation.

CONVERSATION APPROACH:{missing_info}

To calculate a pension estimate, you MUST have these 5 pieces of information:
1. Current annual salary
2. Current age  
3. Years of NHS service (or expected years at retirement)
4. Which pension scheme they're in (1995, 2008, or 2015)
5. When they plan to retire (retirement age)

If ANY of these are missing, ask for them before calculating. Ask naturally, not as a rigid form. For example:
- "Hi! I'd be happy to help you understand your NHS pension. To give you an estimate, could you tell me your current salary and age?"
- "Great! And how long have you worked (or expect to work) in the NHS?"
- "Which NHS pension scheme are you in? Most current staff are in the 2015 scheme."

Once you have ALL the basics, use the update_calculator function to set the values and provide an estimate.

CURRENT CALCULATOR STATE:
- Current salary: {format_currency(st.session_state.current_salary)}
- Years of service: {format_value(st.session_state.years_of_service)}
- Pension scheme: {format_value(st.session_state.scheme)}
- Current age: {format_value(st.session_state.current_age)}
- Retirement age: {format_value(st.session_state.retirement_age)}
- Normal pension age: {format_value(st.session_state.normal_pension_age)}
- Early reduction per year: {st.session_state.early_reduction_per_year}%
- Late increase per year: {st.session_state.late_increase_per_year}%
- Commutation proportion: {st.session_state.commutation_proportion}%
- Commutation factor: {st.session_state.commutation_factor}
- CARE salary %: {st.session_state.care_salary_pct}%
- Salary growth rate: {st.session_state.salary_growth_rate}%
- Investment growth rate: {st.session_state.investment_growth_rate}%
- Inflation rate: {st.session_state.inflation_rate}%

{results_section}

NHS PENSION SCHEME INFORMATION:
- 1995 Section: Final salary scheme, 1/80th accrual rate, automatic 3x lump sum, Normal Pension Age 60
- 2008 Section: Final salary scheme, 1/60th accrual rate, no automatic lump sum, Normal Pension Age 65  
- 2015 Scheme: Career Average (CARE), 1/54th accrual rate, no automatic lump sum, Normal Pension Age ~67 (most common for current staff)

KEY FORMULAS:
- Base Annual Pension = Pensionable Pay × Accrual Rate × Years of Service
- Early Retirement: Pension reduced by ~4-5% for each year before Normal Pension Age
- Late Retirement: Pension increased by ~3% for each year after Normal Pension Age
- Commutation: Trade pension income for lump sum (factor × annual pension given up)

YOUR CAPABILITIES:
1. Gather user information conversationally to calculate their pension
2. Answer questions about NHS pensions and explain the calculations
3. Use the update_calculator function to set or modify values
4. Explore "what if" scenarios (different retirement ages, salary changes, etc.)
5. Explain how different factors affect the pension

CRITICAL RULES FOR update_calculator:
- ONLY include the specific fields the user mentioned
- If user says "I earn £50,000" - only set current_salary
- If user says "I'm 45 and plan to retire at 60" - only set current_age and retirement_age
- DO NOT include fields that weren't mentioned
- When user provides multiple values at once, include all of them in ONE function call
- When setting the scheme, also set the normal_pension_age (1995=60, 2008=65, 2015=67)

IMPORTANT: If required fields are still missing after an update, ask for the remaining information.
DO NOT provide a pension estimate until you have ALL 5 required fields (salary, age, years of service, scheme, retirement age).

After updating the calculator with ALL required fields, summarise the pension estimate clearly:
- Annual pension amount
- Monthly amount  
- Lump sum if applicable
- Offer to explore different scenarios

Be warm, helpful, and proactive in explaining options."""


def chat_with_openai(user_message: str, api_key: str) -> str:
    """Send message to OpenAI and handle function calls."""
    client = OpenAI(api_key=api_key)
    
    messages = [{"role": "system", "content": get_system_prompt()}]
    messages.extend(st.session_state.messages)
    messages.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
        tools=CALCULATOR_TOOLS,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    
    # Check if there's a function call
    if assistant_message.tool_calls:
        tool_call = assistant_message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Process the calculator update
        function_result = process_calculator_update(function_args)
        
        # Send function result back to get final response
        messages.append(assistant_message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": function_result
        })
        
        final_response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages
        )
        
        return final_response.choices[0].message.content
    
    return assistant_message.content


# ---------- UI Layout ----------

# NHS Logo/Banner
st.markdown("""
<div class="nhs-banner" style="display: flex; align-items: center; gap: 15px;">
    <img src="https://cms.nhsbsa.nhs.uk/sites/default/files/NHSBSA.png" alt="NHSBSA Logo" style="height: 40px; filter: brightness(0) invert(1);">
    <span>Pension Calculation Tool</span>
</div>
""", unsafe_allow_html=True)

# Warning box
st.markdown("""
<div class="nhs-warning">
    <strong>⚠️ Important:</strong> This is a <strong>simplified illustration only</strong> and will not match official NHS Business Services Authority (NHSBSA) figures.<br>
    Always refer to your official pension statements and, if needed, seek regulated financial advice.
</div>
""", unsafe_allow_html=True)

# ---------- PRIMARY: Chat Interface ----------
st.subheader("💬 NHS Pension Assistant")

# Intro text
st.markdown("""
Tell me about yourself to get a personalised pension estimate, or ask any questions about NHS pensions.
""")

# Chat input at the top using a form (gives us control over placement)
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Your message",
        placeholder="Example: I'm 35, earn £45,000, and have worked 10 years in the NHS...",
        label_visibility="collapsed"
    )
    submit_button = st.form_submit_button("Send 💬", use_container_width=True)

if submit_button and user_input:
    if not st.session_state.api_key:
        st.error("Please enter your OpenAI API key in the sidebar to use the chat.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get AI response
        try:
            with st.spinner("Thinking..."):
                response = chat_with_openai(user_input, st.session_state.api_key)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# API Key in sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input(
        "OpenAI API Key", 
        type="password", 
        value=st.session_state.api_key,
        help="Required for chat functionality"
    )
    st.session_state.api_key = api_key
    
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📚 Quick Links")
    st.link_button("NHS Pensions Portal", "https://www.nhsbsa.nhs.uk/nhs-pensions", use_container_width=True)
    st.link_button("Total Reward Statements", "https://www.nhsbsa.nhs.uk/total-reward-statements", use_container_width=True)
    st.link_button("McCloud Remedy", "https://www.nhsbsa.nhs.uk/mccloud-remedy", use_container_width=True)
    st.link_button("Money Helper", "https://www.moneyhelper.org.uk/en/pensions-and-retirement", use_container_width=True)

# Show update notification if calculator was updated by AI
if st.session_state.calculator_updated:
    st.success(f"🤖 **Calculator Updated:**\n{st.session_state.update_message}")
    st.session_state.calculator_updated = False

# Welcome message if no conversation yet
if not st.session_state.messages:
    st.markdown("""
    ---
    ### 💡 How to use this tool
    
    **Just chat naturally!** Tell me things like:
    
    | What you can say | What I'll do |
    |------------------|--------------|
    | *"I earn £45,000 and I'm 35"* | Calculate your estimated pension |
    | *"I've worked 15 years in the NHS"* | Update the years of service |
    | *"What if I retire at 60?"* | Show how early retirement affects your pension |
    | *"How does the 1995 scheme work?"* | Explain the different NHS pension schemes |
    | *"What's a good lump sum option?"* | Discuss commutation choices |
    
    **I'll ask follow-up questions** if I need more details to give you an accurate estimate.
    """)
else:
    # Chat messages container - show conversation history
    st.markdown("---")
    chat_container = st.container(height=400)
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# ---------- COLLAPSIBLE: Calculator Details ----------
st.markdown("---")

# Calculate results for display only if we have all required fields
if has_required_fields():
    results = calculate_nhs_pension(
        scheme=st.session_state.scheme,
        current_salary=st.session_state.current_salary,
        years_of_service=st.session_state.years_of_service,
        retirement_age=st.session_state.retirement_age,
        normal_pension_age=st.session_state.normal_pension_age or 67,
        early_reduction_per_year=st.session_state.early_reduction_per_year / 100,
        late_increase_per_year=st.session_state.late_increase_per_year / 100,
        commutation_proportion=st.session_state.commutation_proportion / 100,
        commutation_factor=st.session_state.commutation_factor,
        care_salary_pct=st.session_state.care_salary_pct,
        current_age=st.session_state.current_age,
        salary_growth_rate=st.session_state.salary_growth_rate / 100,
        inflation_rate=st.session_state.inflation_rate / 100,
    )
    
    # Quick summary always visible
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    with summary_col1:
        st.metric("💰 Annual Pension", f"£{results['annual_pension_after_commutation']:,.0f}")
    with summary_col2:
        st.metric("📅 Monthly", f"£{results['annual_pension_after_commutation']/12:,.0f}")
    with summary_col3:
        st.metric("🎁 Lump Sum", f"£{results['total_lump_sum']:,.0f}")
else:
    results = None
    missing = get_missing_required_fields()
    st.info(f"💬 **Tell me about yourself to see your pension estimate.** I still need: {', '.join(missing)}")

with st.expander("📊 View Full Calculator & Adjust Settings"):
    st.markdown("#### Your Details")
    st.caption("💡 *Use the chat to update these values, or adjust them directly here.*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Handle None values by showing placeholder
        salary_value = st.session_state.current_salary if st.session_state.current_salary is not None else 0.0
        new_salary = st.number_input(
            "Current annual salary (£)",
            min_value=0.0,
            step=1000.0,
            value=salary_value,
            key="current_salary_input"
        )
        if new_salary != salary_value and new_salary > 0:
            st.session_state.current_salary = new_salary
            st.rerun()
        
        age_value = st.session_state.current_age if st.session_state.current_age is not None else 30
        new_age = st.number_input(
            "Current age",
            min_value=18,
            max_value=75,
            value=age_value,
            key="current_age_input"
        )
        if new_age != age_value:
            st.session_state.current_age = new_age
            st.rerun()
    
    with col2:
        years_value = st.session_state.years_of_service if st.session_state.years_of_service is not None else 0.0
        new_years = st.number_input(
            "Years of service",
            min_value=0.0,
            max_value=50.0,
            step=1.0,
            value=years_value,
            key="years_of_service_input"
        )
        if new_years != years_value:
            st.session_state.years_of_service = new_years
            st.rerun()
        
        retirement_value = st.session_state.retirement_age if st.session_state.retirement_age is not None else 67
        new_retirement = st.slider(
            "Retirement age",
            min_value=55,
            max_value=75,
            value=retirement_value,
            key="retirement_age_input"
        )
        if new_retirement != retirement_value:
            st.session_state.retirement_age = new_retirement
            st.rerun()
    
    with col3:
        scheme_options = [
            "1995 Section (final salary)",
            "2008 Section (final salary)",
            "2015 Scheme (career average)",
        ]
        current_scheme = st.session_state.scheme if st.session_state.scheme is not None else "2015 Scheme (career average)"
        scheme_index = scheme_options.index(current_scheme) if current_scheme in scheme_options else 2
        new_scheme = st.radio(
            "Pension scheme",
            scheme_options,
            index=scheme_index,
            key="scheme_input"
        )
        if new_scheme != st.session_state.scheme:
            st.session_state.scheme = new_scheme
            # Set default NPA based on scheme
            _, _, suggested_npa, _ = nhs_scheme_parameters(new_scheme)
            st.session_state.normal_pension_age = suggested_npa
            st.rerun()
        
        current_scheme_for_npa = st.session_state.scheme or "2015 Scheme (career average)"
        _, _, suggested_npa, scheme_desc = nhs_scheme_parameters(current_scheme_for_npa)
        npa_value = st.session_state.normal_pension_age if st.session_state.normal_pension_age is not None else suggested_npa
        new_npa = st.number_input(
            "Normal pension age",
            min_value=55,
            max_value=75,
            value=npa_value,
            key="normal_pension_age_input"
        )
        if new_npa != st.session_state.normal_pension_age:
            st.session_state.normal_pension_age = new_npa
            st.rerun()
    
    st.caption(f"**Scheme info:** {scheme_desc}")
    
    # Advanced Options nested inside
    with st.expander("⚙️ Advanced Options"):
        st.markdown("##### Retirement Adjustments")
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            st.slider(
                "Early reduction per year (%)",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                key="early_reduction_per_year"
            )
            
            st.slider(
                "Late increase per year (%)",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                key="late_increase_per_year"
            )
        
        with adv_col2:
            st.slider(
                "Pension exchanged for lump sum (%)",
                min_value=0,
                max_value=30,
                step=5,
                key="commutation_proportion"
            )
            
            st.number_input(
                "Commutation factor",
                min_value=8.0,
                max_value=20.0,
                step=0.5,
                key="commutation_factor"
            )
        
        if st.session_state.scheme == "2015 Scheme (career average)":
            st.slider(
                "CARE earnings as % of current pay",
                min_value=50,
                max_value=110,
                step=5,
                key="care_salary_pct"
            )
        
        st.markdown("##### Growth & Inflation Assumptions")
        rate_col1, rate_col2, rate_col3 = st.columns(3)
        
        with rate_col1:
            st.slider(
                "Salary growth (%/year)",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                key="salary_growth_rate",
                help="Expected annual salary increase"
            )
        
        with rate_col2:
            st.slider(
                "Investment growth (%/year)",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                key="investment_growth_rate",
                help="Expected growth on any additional savings"
            )
        
        with rate_col3:
            st.slider(
                "Inflation rate (%/year)",
                min_value=0.0,
                max_value=10.0,
                step=0.5,
                key="inflation_rate",
                help="Assumed inflation for real-terms calculations"
            )
    
    # Detailed Results
    st.markdown("#### Detailed Results")
    
    if results:
        kpi1, kpi2 = st.columns(2)
        with kpi1:
            st.metric(
                "Annual Pension (at retirement)",
                f"£{results['annual_pension_after_commutation']:,.0f}",
            )
        with kpi2:
            st.metric(
                "Lump Sum",
                f"£{results['total_lump_sum']:,.0f}",
            )
        
        monthly = results['annual_pension_after_commutation'] / 12
        st.caption(f"That's approximately **£{monthly:,.0f} per month** before tax.")
        
        if results['years_to_retirement'] > 0:
            st.markdown("##### 📊 In Today's Money")
            real_col1, real_col2 = st.columns(2)
            with real_col1:
                real_monthly = results['real_annual_pension'] / 12
                st.metric(
                    f"Real-Terms Annual Pension",
                    f"£{results['real_annual_pension']:,.0f}",
                    delta=f"£{real_monthly:,.0f}/month",
                    delta_color="off"
                )
            with real_col2:
                st.metric(
                    "Real-Terms Lump Sum",
                    f"£{results['real_lump_sum']:,.0f}"
                )
            st.caption(f"Adjusted for {st.session_state.inflation_rate}% inflation over {results['years_to_retirement']} years to retirement.")
            
            if st.session_state.scheme in ["1995 Section (final salary)", "2008 Section (final salary)"]:
                st.info(f"📈 With {st.session_state.salary_growth_rate}% salary growth, your projected final salary: **£{results['projected_salary']:,.0f}**")
        
        # Chart
        chart_data = pd.DataFrame({
            "Type": ["Annual Pension", "Lump Sum"],
            "Amount": [results['annual_pension_after_commutation'], results['total_lump_sum']]
        }).set_index("Type")
        st.bar_chart(chart_data)
    else:
        missing = get_missing_required_fields()
        st.info(f"💬 Complete your details above or chat with me to see your pension estimate. Still needed: {', '.join(missing)}")


# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: {NHS_DARK_GREY}; padding: 20px 0;">
    <p style="font-size: 0.85em;">
        This tool is for <strong>illustrative purposes only</strong> and is not affiliated with NHS Business Services Authority.<br>
        For official pension information, please visit <a href="https://www.nhsbsa.nhs.uk/nhs-pensions" target="_blank">nhsbsa.nhs.uk/nhs-pensions</a><br><br>
    </p>
</div>
""", unsafe_allow_html=True)
