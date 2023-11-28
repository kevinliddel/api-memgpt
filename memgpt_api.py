import os
import re

import json
import glob

from typing import Optional
from datetime import date

import memgpt.presets.presets as presets
from memgpt.memory import DummyRecallMemory as RecallMemory
import openai

from pathlib import Path
from memgpt.agent import Agent
from memgpt.config import AgentConfig
from memgpt.humans import humans
from memgpt.interface import CLIInterface as interface
from memgpt.persistence_manager import LocalStateManager
from memgpt.personas import personas

from dotenv import load_dotenv


load_dotenv()
os.environ['MEMGPT_CONFIG_PATH'] = Path.home().joinpath(
    '.memgpt').joinpath('openai_config').as_posix()

openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = 'https://api.openai.com/v1'


PERSONA = os.getenv("PERSONA", personas.DEFAULT)
HUMAN = os.getenv("HUMAN", humans.DEFAULT)
MODEL = os.getenv("MODEL", 'gpt-3.5-turbo-16k')
PRESET = os.getenv("PRESET", presets.DEFAULT_PRESET)
MODEL_ENDPOINT_TYPE = os.getenv("MODEL_ENDPOINT_TYPE", "openai")
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "https://api.openai.com/v1")


def parse_step(contents):
    """
    Parse contents from agent response from step to get full message.

    :param contents: Contents from agent response.
    :return: Full message.
    """
    try:
        message = contents[0][1].get('content', '')
        if contents[0][1].get('function_call'):
            question = json.loads(contents[0][1]['function_call']['arguments'])
            message = '\n' + question.get('message', '')

        return message
    except Exception as err:
        print('Error parsing step contents', str(err))
        return ''


def parse_recall_memory_stats(recall_memory: RecallMemory) -> dict:
    """
    Parse memory from agent response from recall to get full memory.

    :param memory: Memory from agent response.
    :return Stats of memory in dict.
    """
    lines = str(recall_memory).split('\n')
    res = {}

    pattern = re.compile(r'(\d+)\s+([\w\s]+)')
    for line in lines:
        matches = pattern.findall(line)
        for value, key in matches:
            res[key.strip().replace(' ', '_')] = int(value)

    return res


class MemGptAPI():
    """
    API for interacting with memgpt

    :param session_id: Session ID for agent
    """

    def __init__(self, session_id) -> None:
        self.agent_config = AgentConfig(
            name=session_id,
            persona=PERSONA,
            human=HUMAN,
            model=MODEL,
            preset=PRESET,
            model_endpoint_type=MODEL_ENDPOINT_TYPE,
            model_endpoint=MODEL_ENDPOINT,
        )
        self.persistence_manager = LocalStateManager(self.agent_config)

    def check_if_first_message(self) -> bool:
        """
        Check if this is the first message of the conversation

        :return: True if first message, False otherwise
        """
        directory = self.agent_config.save_state_dir()
        if not glob.glob(os.path.join(directory, "*.json")):
            return True

    def init_agent(self) -> Agent:
        """
        Init agent 

        :return: Agent
        """
        agent = presets.use_preset(
            preset_name=PRESET,
            agent_config=self.agent_config,
            model=MODEL,
            persona=PERSONA,
            human=HUMAN,
            interface=interface,
            persistence_manager=self.persistence_manager,
        )
        return agent

    def send_message(self, prompt: str) -> str:
        """
        Send message for existing agent and return response

        :param prompt: Message to send to agent
        :return: Response from agent
        """
        first = self.check_if_first_message()
        agent = self.init_agent() if first else Agent.load_agent(interface, self.agent_config)

        messages = agent.step(user_message=prompt, first_message=False, skip_verify=True)
        agent.save()

        return parse_step(messages)


    def get_recall_memory_stats(self) -> str:
        """
        Get memory from agent

        :return: Memory from agent
        """
        agent: Agent = Agent.load_agent(interface, self.agent_config)
        
        if recall_mem := agent.persistence_manager.recall_memory:
            return parse_recall_memory_stats(recall_mem)


    def search_recall_memory(self, start_date: Optional[date] = None, end_date: Optional[date] = None, text_search: Optional[str] = None) -> list:
        """
        Search memory from agent

        :return: Memory from agent
        """
        agent: Agent = Agent.load_agent(interface, self.agent_config)
        if start_date and end_date:
            messages, count = agent.persistence_manager.recall_memory.date_search(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        elif text_search:
            messages, count = agent.persistence_manager.recall_memory.text_search(text_search)
        return messages if messages else []
