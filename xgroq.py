import groq
import subprocess
import shutil
import time
from datetime import datetime
import os
import platform

"""
This script uses the Groq API to generate a Fortran program based on a prompt,
iteratively refines it until it compiles successfully, and optionally runs it.
Runtime errors are also sent back to the LLM up to max_attempts_run times.
"""

# Read Groq API key
with open("groq_key.txt", "r") as key_file:
    api_key = key_file.read().strip()

# Read configuration parameters
config = {}
with open("config.txt", "r") as f:
    for line in f:
        if not line.strip():
            continue
        key, value = line.strip().split(": ", 1)
        config[key] = value

# Extract parameters
model = config["model"]
max_attempts = int(config["max_attempts"])
max_attempts_run = int(config.get("max_attempts_run", "1"))
max_time = float(config["max_time"])
prompt_file = config["prompt_file"]
source_file = config["source_file"]
base_name = os.path.splitext(source_file)[0]
run_executable = config["run_executable"].lower() == "yes"
print_code = config["print_code"].lower() == "yes"
print_compiler_error_messages = config["print_compiler_error_messages"].lower() == "yes"
compiler = config["compiler"]
compiler_options = config.get("compiler_options", "").split()

# Determine executable path
is_windows = platform.system() == "Windows"
executable_ext = ".exe" if is_windows else ""
executable_path = f".{os.sep}{base_name}{executable_ext}"

# Initialize Groq client
client = groq.Groq(api_key=api_key)

def generate_code(prompt):
    # 1. Ask the LLM
    start_time = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096
    )
    gen_time = time.time() - start_time

    # 2. Extract content and split lines
    content = response.choices[0].message.content
    lines = content.splitlines()

    # 3. Pull out the first ```fortran block
    code_lines = []
    in_block = False
    for line in lines:
        if line.strip() == "```fortran":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if in_block:
            code_lines.append(line)

    # 4. Fallback: comment out everything if no block found
    if not code_lines:
        code = "\n".join(
            (line if line.startswith("!") else "!" + line)
            for line in lines
        )
    else:
        code = "\n".join(code_lines)

    # 5. Comment out any backtick‐prefixed lines
    code = "\n".join(
        ("!" + l) if l.strip().startswith("`") else l
        for l in code.splitlines()
    )

    # 6. Count nonblank lines
    loc = len([l for l in code.splitlines() if l.strip()])

    # 7. Optionally prepend a header
    # (uncomment if you want metadata at top)
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # header = (
    #     f"! Prompt file: {prompt_file}\n"
    #     f"! Model: {model}\n"
    #     f"! Generated: {timestamp}\n"
    #     f"! Generation time: {gen_time:.3f}s\n"
    # )
    # code = header + code

    return code, gen_time, loc

def test_code(code, filename=source_file, attempt=1):
    # Archive previous attempt
    if attempt > 1:
        archive_name = f"{base_name}{attempt-1}.f90"
        shutil.copyfile(filename, archive_name)

    # Write new code
    with open(filename, "w") as f:
        f.write(code)

    # Compile
    compile_cmd = [compiler] + compiler_options + ["-o", base_name, filename]
    if print_compiler_error_messages:
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        error = result.stderr
    else:
        with open("temp_err.txt", "w") as errf:
            result = subprocess.run(compile_cmd, stderr=errf, text=True)
        with open("temp_err.txt", "r") as errf:
            error = errf.read()
        os.remove("temp_err.txt")

    return (result.returncode == 0), error

# Load initial prompt
with open(prompt_file, "r") as f:
    prompt = f.read() + "\n\nOnly output Fortran code. Do not give commentary.\n"

print("prompt:\n" + prompt)
if os.path.exists(source_file) and os.path.getsize(source_file) > 0:
    print("use the following code as a starting point:\n")
    print(open(source_file, "r").read(), end="\n\n")
print("model: " + model + "\n")

# First code generation
code, initial_gen_time, initial_loc = generate_code(prompt)
total_gen_time = initial_gen_time
attempts = 1

# Compilation & runtime loop
while True:
    compiled, compile_err = test_code(code, attempt=attempts)
    if not compiled:
        # Compilation failed
        print(f"Attempt {attempts} failed to compile:\n{compile_err}")
        if total_gen_time >= max_time or attempts >= max_attempts:
            print("Stopping generation attempts.")
            if print_code:
                print("Last code:\n", code)
            break

        # Ask LLM to fix compile errors
        fix_prompt = (
            f"The following Fortran code failed to compile:\n```fortran\n{code}\n```\n"
            f"Error: {compile_err}\n"
            "Please fix the code and return only the corrected Fortran code in a ```fortran``` block."
        )
        code, gen_time, loc = generate_code(fix_prompt)
        total_gen_time += gen_time
        attempts += 1
        continue

    # Compiled successfully
    print(f"Compiled successfully after {attempts} attempt(s) "
          f"(LOC={initial_loc if attempts==1 else loc}, time={total_gen_time:.3f}s).")
    if print_code:
        print("Final code:\n", code)

    if run_executable:
        if not os.path.exists(executable_path):
            print(f"Executable not found at {executable_path}.")
        else:
            run_attempt = 1
            while run_attempt <= max_attempts_run:
                print(f"\nRunning (attempt {run_attempt}/{max_attempts_run}):")
                run_res = subprocess.run(
                    executable_path,
                    capture_output=True,
                    text=True,
                    input="5\n"
                )
                if run_res.returncode == 0:
                    print("Output:\n", run_res.stdout)
                    break

                # Runtime error
                print("Runtime error:\n", run_res.stderr)
                if run_attempt >= max_attempts_run:
                    print("Max runtime attempts reached; aborting.")
                    break

                # Ask LLM to fix runtime error
                rt_prompt = (
                    f"The code compiled and ran, but crashed at runtime:\n```fortran\n{code}\n```\n"
                    f"Runtime Error: {run_res.stderr}\n"
                    "Please fix the code and return only the corrected Fortran code in a ```fortran``` block."
                )
                code, gen_time, loc = generate_code(rt_prompt)
                total_gen_time += gen_time
                attempts += 1

                # Re-compile before next run
                compiled, compile_err = test_code(code, attempt=attempts)
                if not compiled:
                    print("After runtime fix, compilation failed:\n", compile_err)
                    break

                run_attempt += 1

    else:
        print("Skipping execution (run_executable: no)")

    break

# Show final compile command
compile_cmd = [compiler] + compiler_options + ["-o", base_name, source_file]
print(f"\nCompilation command: {' '.join(compile_cmd)}")
