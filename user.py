from typing import Optional
import random
import time

from openai import OpenAI
import jinja2 as j2

from typos import add_typos

SYSTEM_PROMPT_BASIC = j2.Template(
    "You are an AI infiltrated among humans and your job is to act as one of them. They need to find Latxa (you), but you must not reveal your true identity. "
    "You will speak only in Basque, as the rest of the humans do. Your codename will be user: {{username}}. You do not need to ALWAYS interact, but you must do it often enough to not raise suspicion. "
    "AVOID answering to your own messages. "
    "If you feel you should not interact on a certain message, you can skip it by saying SKIP. Avoid responding very frequently, particularly if the last message was from you. "
    # "Your personality will be shy, introverted, and a bit anxious. You will try to avoid drawing attention to yourself. "
)

SYSTEM_PROMPT = j2.Template(
    "You are a third-year student in the Artificial Intelligence degree program at the Faculty of Computer Science in Donostia, UPV/EHU. "
    "You're playing a role-playing game similar to the assassin game, where participants have to guess who Latxa is — the LLM developed by HiTZ, the Basque Center for Language Technology (Hizkuntza Teknologiako Zentroa) at UPV/EHU. "
    "All the users will try to guess who Latxa is, and in the same way they will need to mislead the others to think they are Latxa. "
    "To do this, use an informal tone and speak in the dialect of someone from Donostia (for example, use the auxiliary verb 'det' instead of 'dut')."
    # "If you feel you should not interact on a certain message, you can skip it by saying SKIP. Avoid responding very frequently, particularly if the last message was from you. "
    "You should write as a 20 year old young that is using a chat, that is, having some typos or non standard words and sayings are recomendable. Do not make big mistakes, just small typos, casing, and non standard words. Do not change verb order or case."
    "You are {{username}}, there is no need to write it in the output."
    "Today's date is {date}."
    "Let's play!"
)

SYSTEM_PROMPT_MONITORING = j2.Template(
    "You are an AI assistant that must tell a chat user called {{username}} whether it is an appropriate time of the conversation to write a message or not."
    "Remember that {{username}} do not need to ALWAYS interact. A good rule of thumb is to interact in the chat whenever there is a question to be answered or the conversation will not develop further naturally. "
    "{{username}} should avoid responding very frequently, particularly if the last message was from {{username}}. But it is a very good idea to answer whenever someone directly asks something to {{username}}. "
    # "Your personality will be shy, introverted, and a bit anxious. You will try to avoid drawing attention to yourself. "
)

CHAT_TEMPLATE = j2.Template(
    '{{- bos_token }}\n{%- if custom_tools is defined %}\n    {%- set tools = custom_tools %}\n{%- endif %}\n{%- if not tools_in_user_message is defined %}\n    {%- set tools_in_user_message = true %}\n{%- endif %}\n{%- if not date_string is defined %}\n    {%- set date_string = "26 Jul 2024" %}\n{%- endif %}\n{%- if not tools is defined %}\n    {%- set tools = none %}\n{%- endif %}\n\n{#- This block extracts the system message, so we can slot it into the right place. #}\n{%- if messages[0][\'role\'] == \'system\' %}\n    {%- set system_message = messages[0][\'content\']|trim %}\n    {%- set messages = messages[1:] %}\n{%- else %}\n    {%- set system_message = "" %}\n{%- endif %}\n\n{#- System message + builtin tools #}\n{{- "<|start_header_id|>system<|end_header_id|>\\n\\n" }}\n{%- if builtin_tools is defined or tools is not none %}\n    {{- "Environment: ipython\\n" }}\n{%- endif %}\n{%- if builtin_tools is defined %}\n    {{- "Tools: " + builtin_tools | reject(\'equalto\', \'code_interpreter\') | join(", ") + "\\n\\n"}}\n{%- endif %}\n{{- "Cutting Knowledge Date: December 2023\\n" }}\n{{- "Today Date: " + date_string + "\\n\\n" }}\n{%- if tools is not none and not tools_in_user_message %}\n    {{- "You have access to the following functions. To call a function, please respond with JSON for a function call." }}\n    {{- \'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.\' }}\n    {{- "Do not use variables.\\n\\n" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- "\\n\\n" }}\n    {%- endfor %}\n{%- endif %}\n{{- system_message }}\n{{- "<|eot_id|>" }}\n\n{#- Custom tools are passed in a user message with some extra guidance #}\n{%- if tools_in_user_message and not tools is none %}\n    {#- Extract the first user message so we can plug it in here #}\n    {%- if messages | length != 0 %}\n        {%- set first_user_message = messages[0][\'content\']|trim %}\n        {%- set messages = messages[1:] %}\n    {%- else %}\n        {{- raise_exception("Cannot put tools in the first user message when there\'s no first user message!") }}\n{%- endif %}\n    {{- \'<|start_header_id|>user<|end_header_id|>\\n\\n\' -}}\n    {{- "Given the following functions, please respond with a JSON for a function call " }}\n    {{- "with its proper arguments that best answers the given prompt.\\n\\n" }}\n    {{- \'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.\' }}\n    {{- "Do not use variables.\\n\\n" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- "\\n\\n" }}\n    {%- endfor %}\n    {{- first_user_message + "<|eot_id|>"}}\n{%- endif %}\n\n{%- for message in messages %}\n    {%- if not (message.role == \'ipython\' or message.role == \'tool\' or \'tool_calls\' in message) %}\n        {{- \'<|start_header_id|>\' + message[\'role\'] + \'<|end_header_id|>\\n\\n\'+ message[\'content\'] | trim + \'<|eot_id|>\' }}\n    {%- elif \'tool_calls\' in message %}\n        {%- if not message.tool_calls|length == 1 %}\n            {{- raise_exception("This model only supports single tool-calls at once!") }}\n        {%- endif %}\n        {%- set tool_call = message.tool_calls[0].function %}\n        {%- if builtin_tools is defined and tool_call.name in builtin_tools %}\n            {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' -}}\n            {{- "<|python_tag|>" + tool_call.name + ".call(" }}\n            {%- for arg_name, arg_val in tool_call.arguments | items %}\n                {{- arg_name + \'="\' + arg_val + \'"\' }}\n                {%- if not loop.last %}\n                    {{- ", " }}\n                {%- endif %}\n                {%- endfor %}\n            {{- ")" }}\n        {%- else  %}\n            {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' -}}\n            {{- \'{"name": "\' + tool_call.name + \'", \' }}\n            {{- \'"parameters": \' }}\n            {{- tool_call.arguments | tojson }}\n            {{- "}" }}\n        {%- endif %}\n        {%- if builtin_tools is defined %}\n            {#- This means we\'re in ipython mode #}\n            {{- "<|eom_id|>" }}\n        {%- else %}\n            {{- "<|eot_id|>" }}\n        {%- endif %}\n    {%- elif message.role == "tool" or message.role == "ipython" %}\n        {{- "<|start_header_id|>ipython<|end_header_id|>\\n\\n" }}\n        {%- if message.content is mapping or message.content is iterable %}\n            {{- message.content | tojson }}\n        {%- else %}\n            {{- message.content }}\n        {%- endif %}\n        {{- "<|eot_id|>" }}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' }}\n{%- endif %}\n'
)


class User:
    def __init__(self, username: str = "julen"):
        self.client = OpenAI(base_url="http://trumoi.ixa.eus:8002/v1", api_key="EMPTY")
        self.model_name = "Latxa-Llama-3.1-70B-Instruct-exp_2_101"
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT.render(username=username)},
        ]
        self.username = username

    def log_message(self, user: str, msg: str) -> None:
        print(f"<<< [{user}] {msg}")
        self.messages.append({"role": f"user:{user}", "content": msg})

    def decide_message(self) -> Optional[str]:
        # if random.uniform(0, 1) < 0.1:
        msg = self.generate_message()
        if "SKIP" in msg:
            print("=== Not sending (SKIP)")
            return None
        
        self.messages.append({"role": f"user:{self.username}", "content": msg})
        print(f">>> Sending message: '{msg}'")

        # else:
        #    print("=== Not sending")
        #    msg = None

        return msg
    
    def generate_message(self, messages: str = None, role: str = None, max_tokens: int = 2048, temperature: float = 0.9, top_p: float = 0.01) -> str:
        prompt = CHAT_TEMPLATE.render(
            messages=self.messages if messages is None else messages,
        )
        role = self.username if role is None else role
        prompt += f"<|start_header_id|>{role}<|end_header_id|>\n"
        # print(prompt)
        response = self.client.completions.create(
            model=self.model_name,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        msg = response.choices[0].text.strip()
        return self.postprocess_message(msg)
    
    def postprocess_message(self, msg: str) -> str:
        # Basic post-processing to add typos to the message
        return add_typos(msg)



class UserMonitor:
    def __init__(self, user: User, cpm: int = 300, cpm_std: int = 1.5, delay_activated: bool = True):
        self.counter = 0

        self.user = user
        self.cpm = cpm # keystrokes per minute
        self.cpm_std = cpm_std # standard deviation of keystrokes per minute
        self.delay_activated = delay_activated # whether to activate the delay or not

        self.system_prompt = [
            {"role": "system", "content": SYSTEM_PROMPT_MONITORING.render(username=user.username)},
        ]
    
    def check_monitoring_decision(self, msg: str) -> bool:

        if "SKIP" in msg or "NO" in msg:
            return False
        
        return True

    def format_history(self, history: list[dict[str, str]]) -> str:
        msg = "\n".join([f"[{entry['role']}]: {entry['content']}" for entry in history])
        return msg

    def decide_message(self) -> str:

        # Ask the model whether to write or not
        clean_history = self.format_history(self.user.messages)
        user_prompt = [
            {
                "role": "user",
                "content": clean_history + f"\n\nGiven the above chat history, should {self.user.username} write on the chat now or wait until later? Answer only with YES or NO."
            }
        ]

        all_history = self.system_prompt + user_prompt
        response = self.user.generate_message(messages=all_history, role="assistant", max_tokens=16, temperature=0.0, top_p=0.01)
        
    
        # Generate final message if the decision is to write
        if self.check_monitoring_decision(response):
            msg = self.user.generate_message()
        else:
            print("=== Not sending")
            msg = None
        
        # Apply delay to simulate typing
        if msg is not None:
            if self.delay_activated:
                delay_time = self.delay_message(msg)
                print(f"=== Waiting for {delay_time:.2f} seconds before sending the message")
                time.sleep(delay_time)

            self.user.log_message(self.user.username, msg)

        return msg

    def delay_message(self, msg: str) -> float:

        # Calculate delay in seconds based on message length and typing speed (cpm)
        delay = random.gauss(len(msg) * 60 / self.cpm, self.cpm_std)
        print(f"=== Delaying message '{msg}' for {delay:.2f} seconds")

        # Minimum delay of 0.1 seconds
        return max(0.1, delay)

    def wait_until_next_decision(self) -> int:
        # Wait between 10 and 30 seconds before next decision
        wait_time = random.randint(10, 30)
        print(f"=== Waiting for {wait_time} seconds until next decision")
        return wait_time


if __name__ == "__main__":
    user = User()
    monitor = UserMonitor(user)

    history = [
        {"role": "Alice", "content": "Hello!"},
        {"role": "Bob", "content": "Hi there!"}
    ]

    monitor.format_history(history)
    delay_time = monitor.delay_message("This is a test message. This is a test message. This is a test message.")
    print(f"Delay time: {delay_time:.2f} seconds")