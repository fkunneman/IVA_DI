from collections import defaultdict
from typing import Literal

import chromadb
from django.conf import settings
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from .instruction_agent import InstructAgent


agents: dict[str, InstructAgent] = {}
histories: dict[str, list["Message"]] = defaultdict(list)


class Message:
    message: str
    origin: Literal["person", "agent"]

    def __init__(self, message: str, origin: Literal["person", "agent"]):
        self.message = message
        self.origin = origin


def _prepare_agent(agent: InstructAgent):
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(
        name="instruction_db",
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
    qa_travel = data_path + 'opslag_inclusieve_spraakassistent_project/Vraag_antwoord_ov_v3.csv'
    qa_passport = data_path + 'opslag_inclusieve_spraakassistent_project/Vraag_antwoord_paspoort.csv'
    nav = data_path + 'opslag_inclusieve_spraakassistent_project/navigation.csv'

    agent.prepare_instructions(instructions_travel, 'travel')
    agent.prepare_instructions(instructions_passport, 'passport')
    agent.prepare_patterns(pat)
    agent.setup_rag(collection, [['qa', 'travel', qa_travel], ['qa', 'passport', qa_passport], ['nav', nav]])


def create_agent(model_name: str) -> InstructAgent:
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    chatmodel = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16,
                                                     trust_remote_code=True, device_map="cpu")
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
    _prepare_agent(agent)
    return agent

