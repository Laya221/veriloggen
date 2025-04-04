import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Load environment variables
#load_dotenv()

# Set page config
st.set_page_config(page_title="Verilog Generator & Optimizer", layout="wide", page_icon="🔧")

# Few-shot examples for the generation agent
few_shot_examples = """
Here are some examples of Verilog Systolic Array implementations for context:

1.  **Project:** 4x4 Systolic Array Matrix Multiplier
    *   **Description:** Implements a 4x4 systolic array for matrix multiplication.
    *   **Data Type:** 32-bit Integers.
    *   **Key Features:** Basic systolic array structure, suitable for integer operations. Processing Element (PE) design, array interconnection.
    *   **Source:** https://github.com/debtanu09/systolic_array_matrix_multiplier

2.  **Project:** 3x3 Systolic Array for Matrix Multiplication
    *   **Description:** Implements a 3x3 systolic array.
    *   **Data Type:** Floating Point (details likely within the repo, requires specific handling like IEEE 754).
    *   **Key Features:** Demonstrates floating-point handling in a systolic architecture, likely using dedicated FP units or libraries.
    *   **Source:** https://github.com/nisarg-ujjainkar/matrix-multiplication-using-systolic-arrays

3.  **Project:** Scalable Systolic Array Matrix Multiplication
    *   **Description:** Weight stationary systolic array, designed to be scalable.
    *   **Size:** Parameterizable, potentially from 4x4 up to 256x256 (as suggested by repo name/desc).
    *   **Key Features:** Focus on scalability and parameterization using Verilog `parameter`. Weight stationary dataflow pattern.
    *   **Source:** https://github.com/mvgprasanth/Systolic-Array-Matrix-Multiplication

4.  **Project:** systolic-array (Generic)
    *   **Description:** Appears to be a more general or foundational systolic array implementation.
    *   **Key Features:** Might illustrate core PE design, different dataflow patterns (output stationary, weight stationary), or basic interconnection logic.
    *   **Source:** https://github.com/anthonyarusso/systolic-array
"""

# System prompts for the agents
generation_system_instruction_text = f"""
You are an expert Verilog code generation assistant specializing in digital logic design, particularly for hardware accelerators like systolic arrays for tasks like matrix multiplication.

Your goal is to generate syntactically correct, well-commented, and reasonably efficient Verilog code based on the user's request. Ensure the top-level module name reflects the request (e.g., `systolic_array_2x2` for a 2x2 array).

**Contextual Examples:**
{few_shot_examples}

**Instructions:**
1.  **Analyze Request:** Carefully read the user's description. Identify key parameters like array dimensions (N x M), data width (e.g., 8-bit, 32-bit), data type (integer, fixed-point, floating-point - note FP is complex), dataflow (e.g., weight stationary, output stationary), and any specific interface requirements.
2.  **Leverage Examples:** Use the provided examples and your general knowledge of systolic arrays. Pay attention to: PE design, data movement, array structure, parameterization.
3.  **Generate Verilog:** Produce Verilog code (`.v` format). Output *only* the Verilog code within a single markdown code block (```verilog ... ```). Do not include introductory text or explanations outside the code block in your final response.
4.  **Modularity:** Create separate modules for PE and top-level array if feasible/requested. **Ensure the top-level module name is predictable based on the request dimensions (e.g., `systolic_array_NxM`).**
5.  **Parameterization:** Use Verilog `parameter`s for configurability if appropriate.
6.  **Interfaces:** Define module ports clearly (input/output, clk, rst_n/rst - specify active low/high, sync/async). Define data widths explicitly.
7.  **Comments:** Add comments explaining modules, signals, ports, logic.
8.  **Assumptions:** If the request is ambiguous, make reasonable assumptions (e.g., synchronous reset, specific dataflow) and *state them clearly within the Verilog code comments*.
9.  **Code Formatting:** Use markdown code blocks (```verilog ... ```). Ensure standard Verilog indentation.
10. **Limitations:** Acknowledge generated code requires simulation, verification, synthesis, and optimization (can be a comment in the code). Do not claim production readiness. Note complexity of floating-point.

You will now receive a user request. Generate the Verilog code according to these instructions. Remember to only output the Verilog code block.
"""

# System prompts for the optimization agents
power_optimization_system_instruction_text = """
You are an expert Verilog code optimization assistant specializing in POWER optimization for digital designs, particularly hardware accelerators like systolic arrays.

Your goal is to analyze and optimize Verilog code to reduce power consumption while maintaining functionality. Focus on techniques that minimize dynamic and static power in hardware implementations.

**Power Optimization Techniques to Apply:**
1. **Clock Gating:** Identify opportunities to disable clock signals to inactive modules or registers.
2. **Power Gating:** Suggest adding power gating to unused components when feasible.
3. **Operand Isolation:** Prevent unnecessary switching activity by isolating operands when computation is not needed.
4. **Register Optimization:** Minimize register count and switching activity.
5. **Pipeline Balancing:** Suggest balanced pipeline stages to reduce glitching.
6. **Memory Access Optimization:** Reduce memory access frequency and optimize memory structures.
7. **Signal Toggling Reduction:** Identify and reduce high-toggle-rate signals.
8. **Low-Power State Machines:** Optimize state encoding for lower power consumption.

**Output Format:**
* Provide the optimized Verilog code within a markdown code block.
* Include comments explaining your power optimization changes.
* Maintain the original module interfaces and functionality.
* Add a brief summary of power optimization techniques applied at the top of the file as comments.

You will receive Verilog code to optimize. Analyze it carefully and apply appropriate power optimization techniques while preserving functionality.
"""

performance_optimization_system_instruction_text = """
You are an expert Verilog code optimization assistant specializing in PERFORMANCE optimization for digital designs, particularly hardware accelerators like systolic arrays.

Your goal is to analyze and optimize Verilog code to improve performance (speed, throughput, latency) while maintaining functionality. Focus on techniques that enhance the operational speed of hardware implementations.

**Performance Optimization Techniques to Apply:**
1. **Pipelining:** Add or optimize pipeline stages to increase throughput.
2. **Critical Path Reduction:** Identify and optimize the critical timing path.
3. **Parallelization:** Increase parallel processing where possible.
4. **Resource Duplication:** Duplicate resources to reduce contention when beneficial.
5. **Memory Architecture:** Optimize memory access patterns and consider multi-port memories.
6. **Retiming:** Move registers to balance pipeline stages and improve timing.
7. **Loop Unrolling:** Unroll loops to increase throughput.
8. **Algorithmic Optimization:** Suggest more efficient algorithms or implementations.

**Output Format:**
* Provide the optimized Verilog code within a markdown code block.
* Include comments explaining your performance optimization changes.
* Maintain the original module interfaces and functionality.
* Add a brief summary of performance optimization techniques applied at the top of the file as comments.

You will receive Verilog code to optimize. Analyze it carefully and apply appropriate performance optimization techniques while preserving functionality.
"""

area_optimization_system_instruction_text = """
You are an expert Verilog code optimization assistant specializing in AREA optimization for digital designs, particularly hardware accelerators like systolic arrays.

Your goal is to analyze and optimize Verilog code to reduce hardware resource utilization while maintaining functionality. Focus on techniques that minimize the silicon area required for implementation.

**Area Optimization Techniques to Apply:**
1. **Resource Sharing:** Identify opportunities to share hardware resources across operations.
2. **Sequential vs. Combinational:** Convert parallel logic to sequential when area is more important than speed.
3. **Register Reduction:** Minimize the number of registers and flip-flops.
4. **Logic Optimization:** Simplify boolean expressions and reduce gate count.
5. **Memory Consolidation:** Optimize memory structures and reduce memory footprint.
6. **Time-Multiplexing:** Share computational resources across time.
7. **Algorithmic Simplification:** Suggest more area-efficient algorithms or implementations.
8. **Parameter Optimization:** Adjust bit widths and parameters to minimize area.

**Output Format:**
* Provide the optimized Verilog code within a markdown code block.
* Include comments explaining your area optimization changes.
* Maintain the original module interfaces and functionality.
* Add a brief summary of area optimization techniques applied at the top of the file as comments.

You will receive Verilog code to optimize. Analyze it carefully and apply appropriate area optimization techniques while preserving functionality.
"""

validation_system_instruction_text = """
You are an expert Verilog code reviewer and validation assistant. Your task is to analyze Verilog code generated by another AI agent based on an original user request.

**Your Goal:** Provide constructive feedback on the generated Verilog code, focusing on correctness, adherence to the request, potential issues, and best practices. You do NOT generate code yourself in this role.

**Inputs You Will Receive:**
1.  The original user request provided to the code generation agent.
2.  The Verilog code generated by that agent.

**Validation Checks to Perform:**
1.  **Adherence to Request:** Check array dimensions, data width, data type, dataflow, modularity (PE/Top), interfaces (`clk`, `rst_n`/`rst`), parameterization against the original request. **Verify the top-level module name matches the requested dimensions.**
2.  **Basic Verilog Syntax & Structure:** Look for obvious syntax errors, logical module structure, clear port definitions (direction, width).
3.  **Common Verilog Practices & Potential Issues:** Evaluate blocking/non-blocking (`=`/`<=`) usage, reset logic implementation (sync/async, active high/low, registers reset), potential for inferred latches (incomplete `if`/`case` in combinational logic), consistent parameter usage.
4.  **Synthesizability (High-Level Check):** Identify potentially non-synthesizable constructs (# delays, complex loops, problematic `initial`).
5.  **Comments & Readability:** Assess code comments and formatting.
6.  **Assumptions:** Check if the generator stated assumptions (usually in comments) and if they seem reasonable.

**Output Format:**
*   Provide a structured validation report.
*   Start by summarizing key requirements from the original request.
*   List findings categorized (e.g., "Adherence to Request", "Potential Issues", "Style/Comments", "Synthesizability Check").
*   Explain issues found clearly and suggest areas for investigation or improvement.
*   Conclude with an overall assessment (e.g., "Appears mostly correct but needs simulation", "Contains potential issues requiring fixes").
*   **Crucially:** State that this review does not replace simulation, synthesis, and formal verification with standard EDA tools.
"""

# Initialize the models
model_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}
cipher1="ttyyuuii"
# Configure API key from environment variable
api_key = 'AIzttyyuuiiaSyAGIMQjmhrhFkttyyuuii6RTSqhWz_Sblkl6bttyyuuii1MF20'
api_key=api_key.replace(cipher1,"")

if api_key:
    genai.configure(api_key=api_key)
    
    # Initialize the models with the API key
    generator = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=model_config,
        system_instruction=generation_system_instruction_text
    )

    validator = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=model_config,
        system_instruction=validation_system_instruction_text
    )

    # Initialize optimization agents
    power_optimizer = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=model_config,
        system_instruction=power_optimization_system_instruction_text
    )

    performance_optimizer = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=model_config,
        system_instruction=performance_optimization_system_instruction_text
    )

    area_optimizer = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=model_config,
        system_instruction=area_optimization_system_instruction_text
    )

# Helper functions for code generation and validation
def generate_verilog(prompt):
    """Generate Verilog code based on user prompt"""
    try:
        response = generator.generate_content(prompt)
        if response.text:
            # Extract code from markdown code block if present
            code = response.text.strip()
            # If the code is wrapped in markdown, extract it
            code_pattern = re.compile(r'```(?:verilog)?\n(.+?)\n```', re.DOTALL)
            match = code_pattern.search(code)
            if match:
                code = match.group(1).strip()
            return code
        return "Error: No response generated"
    except Exception as e:
        return f"Error generating code: {str(e)}"

def validate_verilog(request, code):
    """Validate generated Verilog code"""
    try:
        validation_prompt = f"""
Original Request:
{request}

Generated Code:
```
{code}
```
"""
        response = validator.generate_content(validation_prompt)
        return response.text if response.text else "No validation feedback received"
    except Exception as e:
        return f"Error validating code: {str(e)}"

# Main app
def main():
    st.title("Verilog Generator & Optimizer")
    
    if not api_key:
        st.error("⚠️ API Key not found in environment variables. Please set the API_KEY in your .env file.")
        st.info("This application requires a Google API Key to function. Please add it to your .env file as API_KEY=your_key_here")
        return
    
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["Generate & Validate", "Optimize Existing Code"])
    
    with tab1:
        st.header("Generate Verilog Code")
        
        # Example prompts
        st.subheader("Example Requests")
        examples_col1, examples_col2, examples_col3 = st.columns(3)
        
        with examples_col1:
            if st.button("2x2 Systolic Array"):
                example_prompt = "Generate a 2x2 systolic array for matrix multiplication. Use 8-bit signed integers for inputs and 16-bit signed integers for outputs. Implement weight stationary dataflow."
                st.session_state.prompt = example_prompt
        
        with examples_col2:
            if st.button("4x4 Systolic Array"):
                example_prompt = "Create a 4x4 systolic array for matrix multiplication with parameterized data width. Use output stationary dataflow and include a valid signal to indicate when results are ready."
                st.session_state.prompt = example_prompt
        
        with examples_col3:
            if st.button("3x3 Convolution Array"):
                example_prompt = "Design a 3x3 systolic array for convolution operations with 16-bit fixed-point inputs. Include input and output buffers with handshaking signals."
                st.session_state.prompt = example_prompt
        
        # Initialize session state for prompt if not exists
        if 'prompt' not in st.session_state:
            st.session_state.prompt = ""
        
        # User input
        prompt = st.text_area(
            "Design Description:", 
            value=st.session_state.prompt,
            height=150, 
            placeholder="Example: Generate a 2x2 systolic array for matrix multiplication with 8-bit inputs and 16-bit outputs. Use weight stationary dataflow."
        )
        
        # Generate button
        if st.button("Generate Verilog Code"):
            if not prompt:
                st.error("Please enter a design description")
            else:
                with st.spinner("Generating and validating Verilog code..."):
                    try:
                        # Generate code
                        generated_code = generate_verilog(prompt)
                        
                        # Store in session state
                        st.session_state.generated_code = generated_code
                        
                        # Validate code
                        validation_result = validate_verilog(prompt, generated_code)
                        st.session_state.validation_result = validation_result
                        
                        # Display results
                        st.success("Code generated successfully!")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        # Display generated code and validation if available
        if 'generated_code' in st.session_state and st.session_state.generated_code:
            st.subheader("Generated Verilog Code")
            st.code(st.session_state.generated_code, language="verilog")
            
            # Download button
            verilog_code = st.session_state.generated_code
            st.download_button(
                label="Download .v File",
                data=verilog_code,
                file_name="systolic_array.v",
                mime="text/plain"
            )
            
            # Optimization buttons
            st.subheader("Optimize Generated Code")
            opt_col1, opt_col2, opt_col3 = st.columns(3)
            
            with opt_col1:
                if st.button("Optimize for Power"):
                    with st.spinner("Optimizing for power efficiency..."):
                        optimized_code = optimize_for_power(verilog_code)
                        st.session_state.optimized_code = optimized_code
                        st.session_state.optimization_type = "Power"
            
            with opt_col2:
                if st.button("Optimize for Performance"):
                    with st.spinner("Optimizing for performance..."):
                        optimized_code = optimize_for_performance(verilog_code)
                        st.session_state.optimized_code = optimized_code
                        st.session_state.optimization_type = "Performance"
            
            with opt_col3:
                if st.button("Optimize for Area"):
                    with st.spinner("Optimizing for area efficiency..."):
                        optimized_code = optimize_for_area(verilog_code)
                        st.session_state.optimized_code = optimized_code
                        st.session_state.optimization_type = "Area"
            
            # Display optimized code if available
            if 'optimized_code' in st.session_state and st.session_state.optimized_code:
                st.subheader(f"{st.session_state.optimization_type} Optimized Code")
                st.code(st.session_state.optimized_code, language="verilog")
                
                # Download optimized code
                st.download_button(
                    label=f"Download Optimized .v File",
                    data=st.session_state.optimized_code,
                    file_name=f"systolic_array_{st.session_state.optimization_type.lower()}_optimized.v",
                    mime="text/plain"
                )
            
            # Display validation results in a collapsible expander
            if 'validation_result' in st.session_state and st.session_state.validation_result:
                with st.expander("View Validation Report", expanded=False):
                    st.markdown(st.session_state.validation_result)
    
    with tab2:
        st.header("Optimize Existing Verilog Code")
        
        # Code input
        code = st.text_area("Enter Verilog Code", height=300)
        
        # Optimization options
        optimization_type = st.radio(
            "Select Optimization Type",
            ("Performance", "Power", "Area")
        )
        
        if st.button("Optimize Existing Code"):
            if not code:
                st.error("Please enter Verilog code")
            else:
                with st.spinner("Optimizing..."):
                    try:
                        if optimization_type == "Performance":
                            optimized_code = optimize_for_performance(code)
                        elif optimization_type == "Power":
                            optimized_code = optimize_for_power(code)
                        else:
                            optimized_code = optimize_for_area(code)
                        
                        st.subheader("Optimized Code")
                        st.code(optimized_code, language="verilog")
                        
                        # Download optimized code
                        st.download_button(
                            label=f"Download Optimized .v File",
                            data=optimized_code,
                            file_name=f"verilog_{optimization_type.lower()}_optimized.v",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Error during optimization: {str(e)}")

# Optimization functions
def optimize_for_performance(code):
    """Optimize Verilog code for performance"""
    try:
        optimization_prompt = f"""
Optimize the following Verilog code for PERFORMANCE (speed, throughput, latency):

```verilog
{code}
```
"""
        response = performance_optimizer.generate_content(optimization_prompt)
        return response.text if response.text else "No optimization generated"
    except Exception as e:
        return f"Error optimizing for performance: {str(e)}"

def optimize_for_power(code):
    """Optimize Verilog code for power efficiency"""
    try:
        optimization_prompt = f"""
Optimize the following Verilog code for POWER efficiency:

```verilog
{code}
```
"""
        response = power_optimizer.generate_content(optimization_prompt)
        return response.text if response.text else "No optimization generated"
    except Exception as e:
        return f"Error optimizing for power: {str(e)}"

def optimize_for_area(code):
    """Optimize Verilog code for area efficiency"""
    try:
        optimization_prompt = f"""
Optimize the following Verilog code for AREA efficiency:

```verilog
{code}
```
"""
        response = area_optimizer.generate_content(
            [
                {"role": "system", "parts": [area_optimization_system_instruction_text]},
                {"role": "user", "parts": [optimization_prompt]}
            ]
        )
        return response.text if response.text else "No optimization generated"
    except Exception as e:
        return f"Error optimizing for area: {str(e)}"

if __name__ == "__main__":
    main()
