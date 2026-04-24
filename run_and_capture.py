import subprocess, sys
result = subprocess.run(
    [sys.executable, "hosted-agents/src/WebSearchAgent/quick_test.py"],
    capture_output=True, text=True, timeout=90
)
with open("test_output.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nRETURN CODE: {result.returncode}\n")
print("wrote test_output.txt")
