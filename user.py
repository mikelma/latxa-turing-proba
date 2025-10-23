from typing import Optional
import random
import time

from openai import OpenAI
import jinja2 as j2

from typos import add_typos

"""
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
#    "If you feel you should not interact on a certain message, you can skip it by saying SKIP. Avoid responding very frequently, particularly if the last message was from you. "
    "You should write as a 20 year old young that is using a chat, that is, having some typos or non standard words and sayings are recomendable. Do not make big mistakes, just small typos, casing, and non standard words. Do not change verb order or case."
    "You are {{username}}, there is no need to write it in the output."
    "Today's date is {date}."
    "Let's play!"
)

SYSTEM_PROMPT_MONITORING = j2.Template(
    "You are an AI assistant that must tell a chat user called {{username}} whether it is an appropriate time of the conversation to write a message or not."
    "{{username}} needs to interact often enough to not raise suspicion, but not always. "
    "It is a very good idea to answer whenever someone directly asks something to {{username}}. "
    # "Your personality will be shy, introverted, and a bit anxious. You will try to avoid drawing attention to yourself. "
)
"""

CHAT_TEMPLATE = j2.Template(
    '{{- bos_token }}\n{%- if custom_tools is defined %}\n    {%- set tools = custom_tools %}\n{%- endif %}\n{%- if not tools_in_user_message is defined %}\n    {%- set tools_in_user_message = true %}\n{%- endif %}\n{%- if not date_string is defined %}\n    {%- set date_string = "26 Jul 2024" %}\n{%- endif %}\n{%- if not tools is defined %}\n    {%- set tools = none %}\n{%- endif %}\n\n{#- This block extracts the system message, so we can slot it into the right place. #}\n{%- if messages[0][\'role\'] == \'system\' %}\n    {%- set system_message = messages[0][\'content\']|trim %}\n    {%- set messages = messages[1:] %}\n{%- else %}\n    {%- set system_message = "" %}\n{%- endif %}\n\n{#- System message + builtin tools #}\n{{- "<|start_header_id|>system<|end_header_id|>\\n\\n" }}\n{%- if builtin_tools is defined or tools is not none %}\n    {{- "Environment: ipython\\n" }}\n{%- endif %}\n{%- if builtin_tools is defined %}\n    {{- "Tools: " + builtin_tools | reject(\'equalto\', \'code_interpreter\') | join(", ") + "\\n\\n"}}\n{%- endif %}\n{{- "Cutting Knowledge Date: December 2023\\n" }}\n{{- "Today Date: " + date_string + "\\n\\n" }}\n{%- if tools is not none and not tools_in_user_message %}\n    {{- "You have access to the following functions. To call a function, please respond with JSON for a function call." }}\n    {{- \'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.\' }}\n    {{- "Do not use variables.\\n\\n" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- "\\n\\n" }}\n    {%- endfor %}\n{%- endif %}\n{{- system_message }}\n{{- "<|eot_id|>" }}\n\n{#- Custom tools are passed in a user message with some extra guidance #}\n{%- if tools_in_user_message and not tools is none %}\n    {#- Extract the first user message so we can plug it in here #}\n    {%- if messages | length != 0 %}\n        {%- set first_user_message = messages[0][\'content\']|trim %}\n        {%- set messages = messages[1:] %}\n    {%- else %}\n        {{- raise_exception("Cannot put tools in the first user message when there\'s no first user message!") }}\n{%- endif %}\n    {{- \'<|start_header_id|>user<|end_header_id|>\\n\\n\' -}}\n    {{- "Given the following functions, please respond with a JSON for a function call " }}\n    {{- "with its proper arguments that best answers the given prompt.\\n\\n" }}\n    {{- \'Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}.\' }}\n    {{- "Do not use variables.\\n\\n" }}\n    {%- for t in tools %}\n        {{- t | tojson(indent=4) }}\n        {{- "\\n\\n" }}\n    {%- endfor %}\n    {{- first_user_message + "<|eot_id|>"}}\n{%- endif %}\n\n{%- for message in messages %}\n    {%- if not (message.role == \'ipython\' or message.role == \'tool\' or \'tool_calls\' in message) %}\n        {{- \'<|start_header_id|>\' + message[\'role\'] + \'<|end_header_id|>\\n\\n\'+ message[\'content\'] | trim + \'<|eot_id|>\' }}\n    {%- elif \'tool_calls\' in message %}\n        {%- if not message.tool_calls|length == 1 %}\n            {{- raise_exception("This model only supports single tool-calls at once!") }}\n        {%- endif %}\n        {%- set tool_call = message.tool_calls[0].function %}\n        {%- if builtin_tools is defined and tool_call.name in builtin_tools %}\n            {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' -}}\n            {{- "<|python_tag|>" + tool_call.name + ".call(" }}\n            {%- for arg_name, arg_val in tool_call.arguments | items %}\n                {{- arg_name + \'="\' + arg_val + \'"\' }}\n                {%- if not loop.last %}\n                    {{- ", " }}\n                {%- endif %}\n                {%- endfor %}\n            {{- ")" }}\n        {%- else  %}\n            {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' -}}\n            {{- \'{"name": "\' + tool_call.name + \'", \' }}\n            {{- \'"parameters": \' }}\n            {{- tool_call.arguments | tojson }}\n            {{- "}" }}\n        {%- endif %}\n        {%- if builtin_tools is defined %}\n            {#- This means we\'re in ipython mode #}\n            {{- "<|eom_id|>" }}\n        {%- else %}\n            {{- "<|eot_id|>" }}\n        {%- endif %}\n    {%- elif message.role == "tool" or message.role == "ipython" %}\n        {{- "<|start_header_id|>ipython<|end_header_id|>\\n\\n" }}\n        {%- if message.content is mapping or message.content is iterable %}\n            {{- message.content | tojson }}\n        {%- else %}\n            {{- message.content }}\n        {%- endif %}\n        {{- "<|eot_id|>" }}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- \'<|start_header_id|>assistant<|end_header_id|>\\n\\n\' }}\n{%- endif %}\n'
)


class User:
    def __init__(self, user_config: dict, username: str, chat_users: list[str] = None):
        self.client = OpenAI(base_url="http://trumoi.ixa.eus:8002/v1", api_key="EMPTY")
        self.model_name = "Latxa-Llama-3.1-70B-Instruct-exp_2_101"

        self.username = username
        self.chat_users = chat_users if chat_users is not None else []

        self.max_tokens = user_config["generation"]["max_tokens"]
        self.top_p = user_config["generation"]["top_p"]
        self.temperature = user_config["generation"]["temperature"]
        self.user_prompt_template = user_config["generation"]["prompt"]

        self.cpm = user_config["typing"]["cpm"]
        self.cpm_std = user_config["typing"]["cpm_std"]
        self.time_correction = user_config["typing"]["time_correction"]
        self.typo_chance = user_config["typing"]["typo_chance"]
        self.uppercase_chance = user_config["typing"]["uppercase_chance"]

        system_prompt = j2.Template(self.user_prompt_template).render(username=self.username, users=", ".join(self.chat_users[:-1]) + " and " + self.chat_users[-1])
        self.messages = [
            {"role": "system", "content": system_prompt},
        ]


    def log_message(self, user: str, msg: str) -> None:
        print(f"<<< [{user}] {msg}")
        self.messages.append({"role": f"user:{user}", "content": msg})

    def decide_message(self) -> Optional[str]:
        # if random.uniform(0, 1) < 0.1:
        msg = self.generate_message()
        lower_msg = str(msg).lower()
        if "skip" in lower_msg or lower_msg == "none":
            print("=== Not sending (SKIP)")
            return None
        
        self.messages.append({"role": f"user:{self.username}", "content": msg})
        print(f">>> Sending message: '{msg}'")

        # else:
        #    print("=== Not sending")
        #    msg = None

        return msg
    
    def generate_message(self, messages: str = None, role: str = None, max_tokens: int = None, temperature: float = None, top_p: float = None) -> str:
        prompt = CHAT_TEMPLATE.render(
            messages=self.messages if messages is None else messages,
        )
        role = self.username if role is None else role
        prompt += f"<|start_header_id|>{role}<|end_header_id|>\n"
        # print(prompt)
        response = self.client.completions.create(
            model=self.model_name,
            prompt=prompt,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
            temperature=self.temperature if temperature is None else temperature,
            top_p=self.top_p if top_p is None else top_p,
        )
        msg = response.choices[0].text.strip()
        return self.postprocess_message(msg)
    
    def postprocess_message(self, msg: str) -> str:
        # Basic post-processing to add typos to the message
        return add_typos(msg, typo_prob=self.typo_chance, upper_prob=self.uppercase_chance)



class UserMonitor:
    def __init__(self, user: User, config: dict):
        self.counter = 0

        self.user = user

        self.trigger_cooldown = config["proactivity"]["trigger_cooldown"]
        self.trigger_cooldown_std = config["proactivity"]["trigger_cooldown_std"]

        self.rnd_enabled = config["proactivity"]["random_trigger"]["enable"]
        self.rnd_threshold = config["proactivity"]["random_trigger"]["threshold"]

        self.llm_enabled = config["proactivity"]["llm_trigger"]["enable"]
        self.llm_max_tokens = config["proactivity"]["llm_trigger"]["max_tokens"]
        self.llm_temperature = config["proactivity"]["llm_trigger"]["temperature"]
        self.llm_top_p = config["proactivity"]["llm_trigger"]["top_p"]

        self.delay_activated = config["typing"]["enable_delay"]
        
        self.llm_prompt_template = config["proactivity"]["llm_trigger"]["prompt"]
        self.system_prompt = [
            {"role": "system", "content": j2.Template(self.llm_prompt_template).render(username=user.username)},
        ]
    
    def check_monitoring_decision(self, msg: str) -> bool:

        lower_msg = msg.lower()
        if "skip" in lower_msg or "no" in lower_msg:
            return False
        
        return True

    def format_history(self, history: list[dict[str, str]]) -> str:
        msg = "\n".join([f"[{entry['role']}]: {entry['content']}" for entry in history])
        return msg

    def decide_message(self) -> str:
        
        # Generate final message if the decision is to write
        msg = None

        if self.llm_enabled:
            clean_history = self.format_history(self.user.messages)
            user_prompt = [
                {
                    "role": "user",
                    "content": clean_history + f"\n\nGiven the above chat history, should {self.user.username} write on the chat now or wait until later? Answer only with YES or NO."
                }
            ]

            all_history = self.system_prompt + user_prompt
            response = self.user.generate_message(messages=all_history, role="assistant", max_tokens=self.llm_max_tokens, temperature=self.llm_temperature, top_p=self.llm_top_p)
            if self.check_monitoring_decision(response):
                msg = self.user.generate_message()
        
        if self.rnd_enabled:
            if random.uniform(0, 1) < self.rnd_threshold:
                msg = self.user.generate_message()
        
        
        # Apply delay to simulate typing
        if msg is not None and self.delay_activated:
            delay_time = self.delay_message(msg)
            print(f"=== Waiting for {delay_time:.2f} seconds before sending the message")
            time.sleep(delay_time)

        self.user.log_message(self.user.username, msg)

        return msg

    def delay_message(self, msg: str) -> float:

        # Calculate delay in seconds based on message length and typing speed (cpm)
        delay = random.gauss(len(msg) * 60 / self.user.cpm, self.user.cpm_std)
        print(f"=== Delaying message '{msg}' for {delay:.2f} seconds")

        # Minimum delay of 0.1 seconds
        return max(0.1, delay + self.user.time_correction) # Delay minus 5 seconds to account for processing time

    def wait_until_next_decision(self) -> int:
        # Wait some time before next decision
        wait_time = random.gauss(self.trigger_cooldown, self.trigger_cooldown_std)
        print(f"=== Waiting for {wait_time} seconds until next decision")
        return wait_time


if __name__ == "__main__":
    user = User()
    monitor = UserMonitor(user)

    history = [
        {"role": "Alice", "content": "Kaixo!"},
        {"role": "Bob", "content": "Egun on! Nola zaude?"},
    ]

    monitor.format_history(history)
    delay_time = monitor.delay_message("This is a test message. This is a test message. This is a test message.")
    print(f"Delay time: {delay_time:.2f} seconds")
