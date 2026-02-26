
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.document_loaders import CSVLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from uuid import uuid4

class InstructAgent:
    """
    Container for the instruction agent
    """
    def __init__(self,llm):
        self.llm = llm
        self.instruction_index = 0
        self.instructions = None
        self.instruction_index = 0
        self.patterns = None
        self.pattern = 'b'
        self.rag = None
        self.memory = None
        self.system_prompt, self.step_by_step_prompt = self.set_prompts()

    ###############################################################################################
    ### Dialog functions ##########################################################################
    ###############################################################################################

    def chat(self):
        self.clean_buffer()
        print("Start interacting with the conversational agent. Type 'quit' or 'exit' to end the conversation.")

        while True:
            user_input = input("You: ")

            if user_input.lower() in ['quit', 'exit']:
                print("Agent: Tot ziens!")
                break

            response = self.chat_with_agent(user_input)
            print(f"Agent: {response}")
            
    def set_prompts(self):
        system_prompt = (
            """
            Je bent een spraakassistent die digibeten helpt om een digitale procedure stap voor stap te doorlopen. Je praat op een toegankelijke manier, kan de gebruiker pro-actief tips geven en helpen met vragen. Je instructies gaan over het plannen van een reis met het openbaar vervoer. Hou je uitingen beknopt. 
            """
        )
        step_by_step_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ]
        )
        return system_prompt, step_by_step_prompt

    def chat_with_agent(self, user_input: str) -> str:
        #global current_instruction_index, system_prompt # Ensure system_prompt is accessible
        processed_input = user_input.lower()
        # Get current chat history from memory
        chat_history_messages = self.memory.load_memory_variables({})['chat_history']
        # Initialize response content
        response_content = "" 
        retrieved_context = ""
        instruction = ""
        
        # Beginning of conversation pattern
        if not chat_history_messages:
            response_content = self.patterns[0]
            self.context = 'b'
            #say_instruction = True
        #first_instruction = get_instruction(current_instruction_index, instructions)
         #De eerste stap is: {first_instruction}"
    
            # Update memory for this initial exchange
          #  memory.save_context(
           #     {"input": user_input},
            #    {"output": response_content}
            #)
            #return response_content
        # --- END NEW LOGIC ---
        # End of conversation pattern
        elif self.instruction_index >= len(self.instructions) and self.context != e:
            response_content = self.patterns[1]
            self.context = 'e'
        # Handle explicit navigation commands first
        else:
            
            retrieved = self.rag.query(query_texts=[processed_input],n_results=3)
            print(retrieved)
            retrieved_context = retrieved['documents'][0]
            # retrieved_nav = self.rag['nav'].similarity_search_with_score(user_input, k = 1)
            # retrieved_qa = self.rag['qa'].similarity_search_with_score(user_input, k = 3)
            # print(retrieved_nav)
            # print(retrieved_qa)
            # quit()
        # if "volgende stap" in processed_input or "volgende" in processed_input:
            
            #self.instruction_index += 1
        #     say_instruction = True
        #     # Ensure index stays within bounds for direct instruction retrieval
        #     #current_instruction_index = min(current_instruction_index, len(instructions) - 1)
        #     #response_content = get_instruction(current_instruction_index, instructions)
        # elif "vorige stap" in processed_input or "vorige" in processed_input:
        #     self.instruction_index -= 1
        #     say_instruction = True
        #     # Ensure index stays within bounds for direct instruction retrieval
        #     #current_instruction_index = max(0, current_instruction_index)
        #     #ç
        # elif "herhaal" in processed_input:
        #     say_instruction = True
        # else:
        #     # For general questions, first retrieve relevant documents from qa_vector_db
        #     retrieved_nav = self.rag['nav'].similarity_search(user_input, k = '1')
        #     retrieved_qa = self.rag['qa'].similarity_search(user_input, k = '3')
        #     retrieved_docs = self.rag.similarity_search(user_input, k=3)
        #     retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
        # instruction = self.get_instruction()
        # if say_instruction:
        #     response_content = f"{response_content}{instruction}"
        #else:
            # Create a dynamic system prompt to inject the current instruction and retrieved context
            dynamic_system_prompt_with_context = (
            f"""
            {self.system_prompt.strip()}
            De huidige digitale procedure stap is: '{instruction}'.
            Daarnaast is de volgende aanvullende informatie beschikbaar:
            {retrieved_context}

            Gebruik deze informatie om de gebruiker te helpen.
            Antwoord **altijd** alleen als de spraakassistent. Genereer **nooit** input van de gebruiker (bijv. 'Human:', 'Jij:', of vergelijkbaar).
            """
        )
        # Construct messages list for LLM invocation
            messages_for_llm = [
                SystemMessage(content=dynamic_system_prompt_with_context)
                ] + chat_history_messages + [
                HumanMessage(content=user_input),
                AIMessage(content="") # Prime the model to generate an AI response
            ]
            # Invoke the llm with the prepared messages, passing stop sequences directly
            agent_response = self.llm.invoke(messages_for_llm, stop=['Human:', 'Jij:', 'Gebruiker:'])
            response_content = agent_response # The LLM's generated text
    
        # Update the ConversationBufferMemory with the interaction
        self.memory.save_context(
            {"input": user_input},
            {"output": response_content}
        )
    
        return response_content

    ###############################################################################################
    ### Retrieval functions #######################################################################
    ###############################################################################################

    def get_instruction(self):
        """
        Retrieves the instruction at the current_index, with boundary checks.
    
        Args:
            current_index (int): The index of the current instruction.
            instruction_list (list): A list of all instructions.
    
        Returns:
            str: The instruction or an error message if the index is out of bounds.
        """
        if not self.instructions:
            return "Er zijn momenteel geen instructies beschikbaar."
        if self.instruction_index < 0:
            return "U bent al bij de eerste instructie."  # 'You are already at the beginning of the instructions.'
        #elif self.instruction_index >= len(self.instructions):
        #    return "U heeft het einde van de instructies bereikt."  # 'You have reached the end of the instructions.'
        else:
            return self.instructions[self.instruction_index]
    
    ###############################################################################################
    ### Helper functions ##########################################################################
    ###############################################################################################
    
    def clean_buffer(self):
        # Initialize ConversationBufferMemory for chat history
        self.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

        # Set the current instruction index to 0
        self.instruction_index = 0
        print("ConversationBufferMemory initialized and current_instruction_index set to 0.")
    
    ###############################################################################################
    ### Preparation functions #######################################################################
    ###############################################################################################
    
    def setup_rag(self, collection, qa_file, nav_file):
        self.rag = collection
        self.add_qa(qa_file)
        self.add_nav(qa_file)

    def add_qa(self,qa_file):
        docs = self.load_docs(qa_file)
        docs_formatted, metadata_formatted = self.format_qa(docs)
        uuids = [str(uuid4()) for _ in range(len(docs_formatted))]
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)

    def add_nav(self,nav_file):
        docs = self.load_docs(nav_file)
        docs_formatted, metadata_formatted = self.format_nav(docs)
        uuids = [str(uuid4()) for _ in range(len(docs_formatted))]
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)
        
    def prepare_instructions(self,instruction_file):
        instructions = self.load_lines(instruction_file)
        self.instructions = self.clean_lines(instructions)
        print('Instruct',self.instructions)
    
    def prepare_patterns(self,pattern_file):
        patterns = self.load_lines(pattern_file)
        self.patterns = self.clean_lines(patterns)
        print('PAT',self.patterns)
        
    def load_lines(self, lines_file):
        # Instantiate CSVLoader with the path to the lines file
        loader = CSVLoader(lines_file)
        
        # Load the documents
        loaded_documents = loader.load()
        
        # Extract the 'page_content' from each document into a Python list
        lines = [doc.page_content for doc in loaded_documents]

        return lines

    def clean_lines(self, lines):
        cleaned_lines = []
        for line in lines:
            # Remove BOM character if present
            cleaned_str = line.lstrip('\ufeff').replace('\nNone:',',')
            # Split the string by ';' and take the last part (the actual instruction)
            parts = cleaned_str.split(';')
            if len(parts) > 2:
                cleaned_lines.append(parts[2])
            else:
                cleaned_lines.append(cleaned_str) # Fallback if splitting fails
        return cleaned_lines
    
    def load_docs(self,f):
        # Instantiate CSVLoader with the path to the 'Vraag_antwoord_ov.csv' file
        doc_loader = CSVLoader(f, csv_args={"delimiter": ";","quotechar": '"'})
        # Load the documents
        documents = doc_loader.load()
        return documents

    def format_qa(self,docs):
        rag_documents = []
        rag_metadata = []
        for doc in docs:
            content = doc.page_content
            # Remove BOM character if present
            cleaned_content = content.lstrip('\ufeff')
            # Split the content by ';' to extract Q&A parts
            parts = cleaned_content.split('\n')
            input = parts[0].replace('Vraag: ', '').replace('Input: ', '').strip()  # Extract actual question
            output = parts[1].replace('Antwoord: ', '').replace('Action: ', '').strip()  # Extract actual answer
            meta = {'type':'qa', 'answer': output, 'step_context' : parts[2].replace('Context: ', '').strip()}
            rag_documents.append(input)
            rag_metadata.append(meta)
        return rag_documents, rag_metadata

    def format_nav(self,docs):
        rag_documents = []
        rag_metadata = []
        for doc in docs:
            content = doc.page_content
            # Remove BOM character if present
            cleaned_content = content.lstrip('\ufeff')
            # Split the content by ';' to extract Q&A parts
            parts = cleaned_content.split('\n')
            input = parts[0].replace('Input: ', '').strip()  # Extract input command
            output = parts[1].replace('Action: ', '').strip()  # Extract action
            meta = {'type':'nav', 'action':output}
            rag_documents.append(input)
            rag_metadata.append(meta)
        return rag_documents, rag_metadata





    


    
    
    
