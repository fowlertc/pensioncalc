# NHS Pension Planner

A Streamlit-based NHS pension calculator with an integrated AI assistant for exploring pension scenarios.

![NHSBSA Styled](https://img.shields.io/badge/NHSBSA-Styled-005EB8)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)

## Features

### 📊 Pension Calculator
- Support for all NHS pension schemes:
  - **1995 Section** - Final salary, 1/80th accrual, automatic 3x lump sum, NPA 60
  - **2008 Section** - Final salary, 1/60th accrual, NPA 65
  - **2015 Scheme** - Career Average (CARE), 1/54th accrual, NPA ~67
- Early/late retirement adjustments
- Lump sum commutation options
- Projected salary calculations with growth rates
- Real-terms values adjusted for inflation

### 📈 Growth & Inflation Modelling
- Adjustable salary growth rate
- Investment growth rate assumptions
- Inflation rate for real-terms calculations

### 💬 AI Assistant (OpenAI Integration)
- Ask questions about your pension calculations
- Natural language scenario exploration:
  - *"What if I retire at 60?"*
  - *"Change my salary to £55,000"*
  - *"How does the 1995 scheme compare?"*
- AI can directly update calculator values via function calling

### 🎨 NHSBSA Design Standards
- Official NHS Identity colour scheme
- Professional, accessible styling
- Links to official NHS pension resources

## Installation

1. **Create a virtual environment:**
   ```bash
   python -m venv pensions
   ```

2. **Activate the virtual environment:**
   - Windows: `.\pensions\Scripts\Activate.ps1`
   - macOS/Linux: `source pensions/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install streamlit pandas openai
   ```

## Usage

Run the application:
```bash
streamlit run pensions_v2.py
```

The app will open in your browser at `http://localhost:8501`.

### Using the AI Assistant
1. Enter your OpenAI API key in the chat panel
2. Ask questions or request changes to the calculator
3. The AI will update values and explain the impact

## Files

- `pensions.py` - Original single-column layout
- `pensions_v2.py` - Enhanced side-by-side layout with AI-controlled calculator

## Disclaimer

⚠️ **Important:** This is a simplified illustration only and will not match official NHS Business Services Authority (NHSBSA) figures. Always refer to your official pension statements and, if needed, seek regulated financial advice.

## Resources

- [NHS Pensions (Official)](https://www.nhsbsa.nhs.uk/nhs-pensions)
- [Total Reward Statements](https://www.nhsbsa.nhs.uk/total-reward-statements)
- [Member Calculators](https://www.nhsbsa.nhs.uk/member-hub/member-calculators)
- [Scheme Guides](https://www.nhsbsa.nhs.uk/nhs-pensions/nhs-pensions-scheme-guides)
- [McCloud Remedy](https://www.nhsbsa.nhs.uk/mccloud-remedy)

## License

This project is for educational and illustrative purposes only. Not affiliated with NHS Business Services Authority.
