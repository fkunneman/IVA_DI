from collections import defaultdict
from typing import Literal

import chromadb
from django.conf import settings
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import gc

from .instruction_agent import InstructAgent


agents: dict[str, InstructAgent] = {}
histories: dict[str, list["Message"]] = defaultdict(list)

chroma_client = chromadb.Client()


class Message:
    message: str
    origin: Literal["person", "agent"]

    def __init__(self, message: str, origin: Literal["person", "agent"]):
        self.message = message
        self.origin = origin


def _prepare_agent(agent: InstructAgent, agent_id: str):
    collection = chroma_client.create_collection(
        name=f"instruction_db_{agent_id}",
        configuration={
            "hnsw": {
                "space": "cosine",
                "ef_construction": 30
            }
        }
    )
    data_path = str(settings.DATA_PATH) + '/'

    instructions_travel = data_path + 'opslag_inclusieve_spraakassistent_project/instructions_ov_stripped.csv'
    instructions_passport = data_path + 'opslag_inclusieve_spraakassistent_project/instructions_paspoort_stripped_v2.csv'
    pat = data_path + 'opslag_inclusieve_spraakassistent_project/patterns_v2.csv'
    qa_travel = data_path + 'opslag_inclusieve_spraakassistent_project/Vraag_antwoord_ov_v5.csv'
    qa_passport = data_path + 'opslag_inclusieve_spraakassistent_project/Vraag_antwoord_paspoort.csv'
    nav = data_path + 'opslag_inclusieve_spraakassistent_project/navigation.csv'

    agent.set_logger(str(settings.LOGGING_PATH))
    agent.prepare_instructions(instructions_travel, 'travel')
    agent.prepare_instructions(instructions_passport, 'passport')
    agent.prepare_patterns(pat)
    agent.setup_rag(collection, [['qa', 'travel', qa_travel], ['qa', 'passport', qa_passport], ['nav', nav]])


def create_agent(model_name: str, agent_id: str) -> InstructAgent:
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    chatmodel = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16,
                                                     trust_remote_code=True, device_map=settings.DEVICE)
    # set pipeline
    pipe = pipeline(
        "text-generation",
        model=chatmodel,
        tokenizer=tokenizer,
        return_full_text=False,
        max_new_tokens=250,  # Limit the number of generated tokens for concise responses
        do_sample=True,  # Enable sampling for more varied responses
        temperature=0.7  # Control creativity
    )
    llm = HuggingFacePipeline(pipeline=pipe)
    agent = InstructAgent(llm)
    agent.model_name = model_name
    agent.clean_buffer()
    agent.context = 'b'
    _prepare_agent(agent, agent_id)
    return agent


def discard_agent(identifier: str):
    agents.pop(identifier, None)
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
        print(torch.cuda.memory_summary())
