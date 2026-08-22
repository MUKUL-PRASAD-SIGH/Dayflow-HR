"""
Script to run debug_leave.py and save output to a file
"""
import subprocess
import sys

def main():
    print("Running debug script and saving output to debug_output.txt...")
    with open('debug_output.txt', 'w') as f:
        try:
            # Run the debug script and capture both stdout and stderr
            result = subprocess.run(
                [sys.executable, 'debug_leave.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True
            )
            f.write(result.stdout)
            print("✅ Debug output saved to debug_output.txt")
        except subprocess.CalledProcessError as e:
            f.write(f"Error running debug script:\n{e.output}")
            print(f"❌ Error running debug script. Output saved to debug_output.txt")

if __name__ == "__main__":
    main()
