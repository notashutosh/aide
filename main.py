import pty
import os
from openai import OpenAI
import subprocess
client = OpenAI()

def spawn_shell():
    while True:
        try:
            line = input("$ ")
            master, slave = pty.openpty()
            pid = os.fork()
            if pid == 0:  # Child process
                os.close(master)
                os.dup2(slave, 0)  # Redirect stdin
                os.dup2(slave, 1)  # Redirect stdout
                os.dup2(slave, 2)  # Redirect stderr
                os.execvp("sh", ["sh", "-c", line])
            else:  # Parent process
                os.close(slave)
                while True:
                    try:
                        output = os.read(master, 1024)
                        if not output:
                            break
                        decoded_output = output.decode()
                        if "command not found" in decoded_output:
                            response = client.responses.create(
                                model="gpt-4o",
                                input=f'{line}. I am running a mac. Give me just the command so I can run it in my terminal. Do not include any explanation or additional text.',
                                temperature=0
                            )
                            command = response.output_text.split("```bash")[1].split("```")[0].strip()
                            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            print(result.stdout, end="")
                        else:
                            print(decoded_output, end="")
                    except OSError:
                        break
                os.waitpid(pid, 0)
        except EOFError:
            print("\nExiting...")
            break

if __name__ == "__main__":
    if os.system("which openai > /dev/null 2>&1") != 0:
        print("The 'openai' command is not installed. Nothing will work.")
        exit(1)
    else:
        print('openai found')
    
    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
        print("Error: The 'OPENAI_API_KEY' environment variable is not set. Please set it and try again.")
        exit(1)
    else:
        print('openai api key found')
    
    spawn_shell()