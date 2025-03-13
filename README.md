# Groq-Fortran-agent
Python script that uses LLMs on Groq to create Fortran programs, iterating with compiler error messages until they compile. All attempts are saved,
with names such as foo1.f90, foo2.f90 etc. It has been tested on Windows but may run on other operating systems. It works with `ifx` as well
as `gfortran`, with a suitable value for `compiler_options`.

Running `python xgroq.py` for a configuration file

```
model: qwen-2.5-coder-32b
max_attempts: 10
max_time: 1000
prompt_file: prompt_cauchy.txt
source_file: cauchy.f90
run_executable: yes
print_code: no
print_compiler_error_messages: no
compiler: gfortran
compiler_options: -O0 -Wall -Werror=unused-parameter -Werror=unused-variable -Werror=unused-function -Wno-maybe-uninitialized -Wno-surprising -fbounds-check -static -g
```
where the `prompt_cauchy.txt` contains
```
Do a Fortran simulation to find the optimal trimmed mean estimator of
the location of the Cauchy distribution, trying trimming proportions
of 0%, 10%, 20%, 30%, 40%, and 45%. Declare real variables as
real(kind=dp) with dp a module constant, and put procedures in a
module. Have the simulation use 100 samples of 1000 observations each.
```
sample output is
```
Attempt 1 failed (error details suppressed, generation time: 3.164 seconds, LOC=67)
Attempt 2 failed (error details suppressed, generation time: 14.672 seconds, LOC=71)
Code compiled successfully after 3 attempts (generation time: 18.061 seconds, LOC=75)!
Running executable: .\cauchy.exe

Output:
  Trim proportion:   0.0000000000000000      Mean trimmed mean:  -2.7425188462552290
 Trim proportion:  0.10000000000000001      Mean trimmed mean:   1.6141409422076695E-002
 Trim proportion:  0.20000000000000001      Mean trimmed mean:   1.4961654913832745E-002
 Trim proportion:  0.29999999999999999      Mean trimmed mean:   1.2341060294325419E-002
 Trim proportion:  0.40000000000000002      Mean trimmed mean:   1.1169627560190555E-002
 Trim proportion:  0.45000000000000001      Mean trimmed mean:   1.0791625569573506E-002

Total generation time: 35.897 seconds across 3 attempts

Compilation command: gfortran -O0 -Wall -Werror=unused-parameter -Werror=unused-variable -Werror=unused-function -Wno-maybe-uninitialized -Wno-surprising -fbounds-check -static -g -o cauchy cauchy.f90
```
