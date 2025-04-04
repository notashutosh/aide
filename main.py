import pty
import os
from openai import OpenAI
import subprocess
import readline
from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
import ptyprocess
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.widgets import TextArea, Label, Frame
from prompt_toolkit.application import Application
import asyncio

client = OpenAI()

def spawn_shell():
    while True:
        try:
            bindings = KeyBindings()

            @bindings.add("c-t")  # Detect Control+T
            def _(event):
                process = ptyprocess.PtyProcess.spawn(["sh"])
                print("Ctrl+T pressed—Choose an option (doesn't really matter what you choose):")
                print("1) Create recipe")
                print("2) Edit recipe")
                while True:
                    user_input = input("Enter your choice (1/2): ").strip().lower()
                    if user_input in ["1", "2"]:
                        instruction_box = TextArea(prompt="Instruction: ")
                        final_result_box = TextArea(prompt="Final Result: ")
                        output_file_box = TextArea(prompt="Output File: ")

                        layout = Layout(
                            HSplit([
                                VSplit([
                                    HSplit([
                                        Frame(title="Instruction", body=instruction_box),
                                        Frame(title="Final Result", body=final_result_box),
                                    ]),
                                    Frame(title="Output File", body=output_file_box),
                                ])
                            ])
                        )
                        break
                    else:
                        print("Invalid choice. Please enter '1' or '2'.")
                app = Application(layout=layout, full_screen=True, key_bindings=KeyBindings())

                @app.key_bindings.add("c-d")  # Detect Control+D
                def _(event):
                    event.app.exit()
                
                @app.key_bindings.add("tab")  # Detect Tab key
                def _(event):
                    event.app.layout.focus_next()
                try:
                    # Use `await` directly if the event loop is already running
                    asyncio.create_task(app.run_async())
                except KeyboardInterrupt:
                    print("\nOperation canceled by user.")
                process.terminate()
                

            line = prompt("$ ", key_bindings=bindings)
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
                            try:
                                command = response.output_text.split("```bash")[1].split("```")[0].strip()
                            except (IndexError, AttributeError):
                                print("I don't understand what you want")
                                continue
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