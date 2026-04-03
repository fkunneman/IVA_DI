
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
import time
import numpy
from scipy.sparse import csr_matrix

class InstructAgent:
    """
    Container for the instruction agent
    """
    def __init__(self,llm,tokenizer,dct,tfidf):
        self.llm = llm
        self.tokenizer = tokenizer
        self.dct = dct
        self.tfidf = tfidf
        self.instruction_index = 0
        self.context = None
        self.prev_context = None
        self.domain = None
        self.instructions = {}
        self.active_instructions = []
        self.patterns = None
        self.pattern = 'b'
        self.rag = None
        self.memory = None
        self.last = None
        # self.system_prompt = self.set_system_prompt()

    ###############################################################################################
    ### Dialog functions ##########################################################################
    ###############################################################################################

    def chat(self):
        self.clean_buffer()
        self.context = 'b'
        print(self.patterns[0])
        while True:
            user_input = input("You: ")
            response = self.chat_with_agent(user_input)
            print(f"Agent: {response}")
            if response == "Tot ziens!":
                break


    def get_system_prompt(self):
        # custom system prompts per domain to reduce processing time
        if self.domain == 'travel':
            role = (
                """  
                Je bent een spraakassistent die digibeten helpt om een digitale procedure stap voor stap te doorlopen. Dit doe je door instructies te geven die de gebruiker uitvoert. Je instructies gaan over het plannen van een reis met het openbaar vervoer via de website 9292.nl
            De gebruiker probeert de instructies op een laptopscherm uit te voeren en hoeft in reactie op je instructies niet informatie te geven zoals vertrektijd, locatie of persoonlijke gegevens. 
            Maak korte zinnen. Je kan de gebruiker tips geven en helpen met vragen. Hou je uitingen beknopt. Formuleer strikt een reactie op de gebruiker. Formuleer niet uit jezelf een instructie. 
                """
            )
            interface = (
                """
                User interface reis plannen:
    
                Velden:
                - 'van' (vertrekpunt)
                - 'naar' (bestemming)
    
                Knoppen
                - 'nu' (standaard instelling)
                - 'vertrek'
                - 'aankomst'
                - 'datum' (date picker)
                - 'tijd' (time picker)
                - 'plan je reis'
    
                Gedrag interface:
    
                - 'vertrek': de gebruiker kiest vertrekdag met 'datum' en vertrektijd met 'tijd'
                - 'aankomst': de gebruiker kiest de aankomstdag met 'datum' en aankomsttijd met 'tijd'
                """
            )
        elif self.domain == 'passport':
            role = (
                """  
                Je bent een spraakassistent die digibeten helpt om een digitale procedure stap voor stap te doorlopen. Dit doe je door instructies te geven die de gebruiker uitvoert. Je instructies gaan over het inplannen van een afspraak om een paspoort aan te vragen bij de gemeente amsterdam. 
            De gebruiker probeert de instructies op een laptopscherm uit te voeren en hoeft in reactie op je instructies niet informatie te geven zoals locatie of persoonlijke gegevens. 
            Maak korte zinnen. Je kan de gebruiker tips geven en helpen met vragen. Hou je uitingen beknopt. Formuleer strikt een reactie op de gebruiker. Formuleer niet uit jezelf een instructie.
                """
            )
            interface = (
                """
                User interface paspoort aanvragen:
    
                Venster 1: homepage
    
                Clickable text:
                - 'Verhuizing doorgeven'
                - 'Paspoort, ID-kaart en rijbewijs'
    
                Gedrag venster 1:
                - 'Paspoort, ID-kaart en rijbewijs' staat onder 'Verhuizing doorgeven'
                - Clickable text wordt weergegeven in blauw, kan gebruiker op klikken
    
                Venster 2:
    
                Clickable text:
                - Paspoort 18 jaar en ouder
    
                Section headers:
                -'Paspoort aanvragen'
                -'ID-kaart aanvragen'
    
                Gedrag venster 2:
                - Clickable text wordt weergegeven in blauw en kan worden aangeklikt door de gebruiker.
                - Klikken opent de bijbehorende pagina of sectie.
                - Section headers zijn zwarte tekst en staan boven de kolommen.
                - 'Paspoort 18 jaar en ouder' staat onder section header 'Paspoort aanvragen'
    
                Venster 3:
    
                Section:
                - 'Aanvragen'
    
                Clickable text:
                - 'Afspraak maken'
                - 'Adressen en openingstijden stadsloketten'
    
                Gedrag venster 3:
                - Section headers zijn in zwarte tekst
                - Section 'Aanvragen' staat boven clickable text 'afspraak maken'
    
                Venster 4 (form):
    
                Velden:
                - 'Persoon/personen' (getal)
                - 'Locatie' (radio buttons)
                - 'Achternaam'
                - 'Voornaam'
                - 'Geboortedatum'
                - 'E-mailadres'
                - 'Mobiel telefoonnummer'
    
                Knoppen:
                - '+'
                - '-'
                - Date picker (datum afspraak)
                - 'Beschikbare tijden'
                - Date picker (geboortedatum)
                - 'Land code' (dropdown)
                - 'Maak afspraak'
                - 'Opnieuw beginnen'
    
                Gedrag interface:
    
                - '+': user verhoogt het getal in veld 'Persoon/personen', het aantal personen waarvoor paspoort wordt aangevraagd met 1
                - '-': user verlaagt het getal in veld 'Persoon/personen', het aantal personen waarvoor paspoort wordt aangevraagd met 1
                - De user kan om een geboortedatum in te vullen het veld 'Geboortedatum' gebruiken of de date picker
                - De user is niet verplicht om een telefoonnummer in te vullen
                """
            )
        return role, interface

    def chat_with_agent(self, user_input: str) -> str:
        #global current_instruction_index, system_prompt # Ensure system_prompt is accessible
        processed_input = user_input.lower()
        #query_embedding = self.embedding_model.encode([processed_input])
        #self.tokenizer.process(processed_input)
        #query_tokenized = [x.text for x in self.tokenizer]
        #query_bow = self.dct.doc2bow(query_tokenized)
        # query_tfidf = self.tfidf[query_bow]
        # query_weights = [x[1] for x in query_tfidf]
        #qvector = numpy.zeros((len(self.tfidf.idfs), ), float)
        #tfidf = self.tfidf[query_bow]
        #for index, value in tfidf:
        #    qvector[index] = value
        # for w in query_bow:
        #     qvector[w[0]] = self.tfidf.idfs[w[0]]
        # qvector_np = numpy.array(qvector)
        # Get current chat history from memory
        chat_history_messages = self.memory.load_memory_variables({})['chat_history']
        prompt = False
        if self.domain == None:
            retrieved = self.rag.query(query_texts=processed_input,n_results=3,where={'$and': [{'type': 'nav'}, {'step_context': {'$in': ['all',self.context]}}]})
            #retrieved = self.rag.query(query_embeddings=qvector,n_results=3,where={'$and': [{'type': 'nav'}, {'step_context': {'$in': ['all',self.context]}}]})
        else:
            retrieved = self.rag.query(query_texts=processed_input,n_results=3,where={'$and': [{'type': {'$in': ['nav',self.domain]}}, {'step_context': {'$in': ['all',self.context]}}]})
            #retrieved = self.rag.query(query_embeddings=qvector,n_results=3,where={'$and': [{'type': {'$in': ['nav',self.domain]}}, {'step_context': {'$in': ['all',self.context]}}]})
        match,distance,cat,do = self.parse_retrieved(retrieved)
        print('MATCH',match,', DISTANCE',distance,', CAT',cat,', DO',do,'CONTEXT',self.context)
        response_content, prompt, dynamic_system_prompt_with_context = self.select_response(processed_input,match,distance,cat,do)
        if prompt:
            print('dynamic system prompt',dynamic_system_prompt_with_context)
            start_time = time.perf_counter()
            # Construct messages list for LLM invocation
            messages_for_llm = [
                SystemMessage(content=dynamic_system_prompt_with_context)
                ] + chat_history_messages + [
                HumanMessage(content=user_input),
                AIMessage(content="") # Prime the model to generate an AI response
            ]
            # Invoke the llm with the prepared messages, passing stop sequences directly
            agent_response = self.llm.invoke(messages_for_llm, stop=['Human:', 'Jij:', 'Gebruiker:'], max_tokens=250)
            response_content = agent_response.split('Human:')[0] # The LLM's generated text
            if len(response_content) > 250:
                response_content = '.'.join(response_content.split('.')[:-1])
            elapsed_time = time.perf_counter() - start_time
            print('Prompt took',elapsed_time)
        # Update the ConversationBufferMemory with the interaction
        self.memory.save_context(
            {"input": user_input},
            {"output": response_content}
        )
        self.last = [processed_input,match,distance,cat,do]
        return response_content

    def select_response(self,processed_input,match,distance,cat,do):
        print('sel_res',match,distance,cat,do)
        prompt = False
        # Initialize response content
        response_content = ""
        retrieved_context = ""
        instruction = ""
        dynamic_system_prompt_with_context = ""
        if distance >= 0.70:
           if self.context == 'b':
                response_content = f"Ik verstond '{processed_input}'. Ik verwachtte dat je zou kiezen voor 'een reis plannen' of 'een afspraak maken voor een paspoort'. Voor welke van de twee kies je?"
           else:
                prompt = True
                role, interface = self.get_system_prompt()
                dynamic_system_prompt_with_context = (
                f"""
                {role}
                'Formuleer een reactie op de uiting van de gebruiker. De laatste instructie die je gegeven hebt is: '{self.get_instruction()}'
                Als de uitspraak van de gebruiker niet past in de context, geef dan aan dat je de vraag niet kunt beantwoorden en herhaal de laatste instructie of vraag de gebruiker om 'vorige' of 'volgende' te zeggen.'
                {interface}
                """
                )
        elif distance >= 0.50 and distance < 0.70:
            response_content = f"""Bedoelde je "{match[0]}"?"""
            self.prev_context = self.context
            self.context = 'd'
        elif cat == 'nav':
            if do == 'clarify':
                if self.context == 'b':
                    response_content = f"Er zijn twee dingen waar ik je bij kan helpen: een reis plannen op 9292.nl of een afspraak inplannen voor een paspoort bij de gemeente Amsterdam. Ik hoor graag van je welke van de twee instructies je wil horen." 
                else:
                    prompt = True
                    role, interface = self.get_system_prompt()
                    dynamic_system_prompt_with_context = (
                    f"""
                    {role}
                    \nDe huidige instructie is: '{self.get_instruction()}'
                    \nDe gebruiker vraagt om een verduidelijking van de instructie. Formuleer deze verduidelijking op een manier dat een digibeet het snapt, maar maak het niet te kinderlijk. Richt je met de verduidelijking op de gebruiker. Geef alleen de verduidelijking en geen andere toevoegingen. Formuleer gee nieuwe instructiestap.'  
                    {interface}
                    """
                    )
            elif do == 'Done':
                if self.context == 'e':
                    response_content = 'Tot ziens!'
                else:
                    response_content = f"Je zegt '{processed_input}'. Weet je zeker dat je wil stoppen met het gesprek?"
                    self.context = 'q'
            elif do == 'Confirm':
                if self.context == 'q':
                    response_content = 'Tot ziens!'
                elif self.context in ['p','t']:
                    if self.context == 'p':
                        self.domain = 'passport'
                        self.instruction_index = 0
                        response_start = self.navigate('passport',processed_input)
                    elif self.context == 't':
                        self.domain = 'travel'
                        self.instruction = 0
                        response_start = self.navigate('travel',processed_input)
                    instruction = self.get_instruction()
                    response_content = f"{response_content}{response_start}{instruction}"
                    # End of conversation pattern
                    if self.instruction_index == (len(self.active_instructions)-1) and self.context != 'e':
                        response_content = f"{response_content} {self.patterns[1]}"
                        self.context = 'e'
                elif self.context == 'd':
                    self.context = self.prev_context
                    response_content, prompt, dynamic_system_prompt_with_context = self.select_response(self.last[0],self.last[1],0.1,self.last[3],self.last[4])
                else:
                    response_content = f"Ik verstond '{processed_input}', maar verwacht hier geen antwoord. Zeg 'volgende' als je naar de volgende instructie wil, of stel een vraag over de huidige instructie."  
            elif do == 'Reject':
                if self.context == 'q' or self.context == 'p' or self.context == 't':
                    response_content = f"Okay! De huidige instructie is: '{self.get_instruction()}' Laat het me weten als je hier vragen over hebt of naar de volgende instructie wil."
                    try:
                        self.context = str(self.instruction_index+1)
                    except:
                        self.context = self.context
                elif self.context == 'd':
                    response_content = f"Okay! Zou je het dan nog een keer willen zeggen, in iets andere woorden?"
                    self.context = self.prev_context
                else:
                    response_content = f"Ik verstond '{processed_input}', maar verwacht hier geen antwoord. Zeg 'volgende' als je naar de volgende instructie wil, of stel een vraag over de huidige instructie."  
            else:
                response_start = self.navigate(do,processed_input)
                if not self.context in ['t','p']:
                    instruction = self.get_instruction()
                    response_content = f"{response_content}{response_start}{instruction}"
                else:
                    response_content = response_start
                # End of conversation pattern
                if self.instruction_index == (len(self.active_instructions)-1) and self.context != 'e':
                    response_content = f"{response_content} {self.patterns[1]}"
                    self.context = 'e'
        elif cat == self.domain:
            response_content = do
        return response_content, prompt, dynamic_system_prompt_with_context
        
    def navigate(self,do,inp):
        # perform the fitting navigation and add the fitting response
        if do == 'travel': # start ov instructions
            if self.domain == 'passport':
                response_start = f"Ik verstond '{inp}'. We doorlopen nu andere instructies. Weet je zeker dat je liever de instructies voor het plannen van een reis met het OV wil horen?"
                self.context = 't'
                return response_start
            else: # domain = travel
                if self.instruction_index > 0:
                    response_start = f"Klopt het dat je vraagt om de instructies voor het plannen van een reis met het ov? We zijn nu bij stap '{self.context}'. Wil je naar het begin van de instructies?"
                    self.context = 't'
                else:
                    self.active_instructions = self.instructions[do]
                    self.domain = 'travel'
                    response_start = 'Ik ga je instrueren om een reis met het ov te plannen op 9292.nl. Stap 1: '
        elif do == 'passport': # start passport instructions
            if self.domain == 'travel':
                response_start = f"Ik verstond '{inp}'. We doorlopen nu andere instructies. Weet je zeker dat je liever de instructies voor het aanvragen van een paspoort wil horen?"
                self.context = 'p'
                return response_start
            else:
                if self.instruction_index > 0:
                    response_start = f"Klopt het dat je vraagt om de instructies voor het aanvragen van een paspoort? We zijn nu bij stap '{self.context}'. Wil je naar het begin van de instructies?"
                    self.context = 'p'
                else:
                    self.active_instructions = self.instructions[do]
                    self.domain = 'passport'
                    response_start = 'Ik ga je instrueren om een paspoort aan te vragen op de website van de gemeente Amsterdam. Stap 1: '
        elif do == 'next step': # move to next step
            if self.domain != None:
                self.instruction_index += 1
            response_start = ''
        elif do == 'current step': # repeat current step
            response_start = ''
        elif do == 'previous step': # move to next step
            if self.instruction_index == 0:
                response_start = 'Je zit al bij stap 1, dus ik kan geen stap terug instrueren. '
            else:
                self.instruction_index -= 1
                response_start = 'De vorige stap is: '

        try:
            self.context = str(self.instruction_index+1)
        except:
            self.context = self.context
        return response_start

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
        if not self.active_instructions:
            return "Er zijn momenteel geen instructies beschikbaar."
        if self.instruction_index < 0:
            return "U bent al bij de eerste instructie."  # 'You are already at the beginning of the instructions.'
        elif self.instruction_index >= len(self.active_instructions):
            return "U heeft het einde van de instructies bereikt."  # 'You have reached the end of the instructions.'
        else:
            return self.active_instructions[self.instruction_index]

    def parse_retrieved(self,retrieved):
        #print(retrieved)
        match = retrieved['documents'][0]
        distance = retrieved['distances'][0][0]
        meta = retrieved['metadatas'][0][0]
        cat = meta['type']
        do = meta['action'] if cat == 'nav' else meta['answer']
        return match,distance,cat,do


    ###############################################################################################
    ### Helper functions ##########################################################################
    ###############################################################################################

    def clean_buffer(self):
        # Initialize ConversationBufferMemory for chat history
        self.memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)

        # Set the current instruction index to None
        self.instruction_index = 0

    ###############################################################################################
    ### Preparation functions #######################################################################
    ###############################################################################################

    def setup_rag(self, collection, rag_files):
        self.rag = collection
        for entry in rag_files:
            if entry[0] == 'qa':
                self.add_qa(entry[1],entry[2])
            elif entry[0] == 'nav':
                self.add_nav(entry[1])

    def add_qa(self,domain,qa_file):
        docs = self.load_docs(qa_file)
        docs_formatted, metadata_formatted = self.format_qa(domain,docs)
        uuids = [str(uuid4()) for _ in range(len(docs_formatted))]
        # docs_tokenized = []
        # for doc in docs_formatted:
        #     self.tokenizer.process(doc)
        #     tokenized = [x.text for x in self.tokenizer]
        #     docs_tokenized.append(tokenized)
        # docs_bow = [self.dct.doc2bow(doc) for doc in docs_tokenized]
        # #docs_vectors = numpy.zeros((len(docs_bow),len(self.tfidf.idfs)), float)
        # row = []
        # col = []
        # data = []
        # for i,doc in enumerate(docs_bow):
        #     tfidf = self.tfidf[doc]
        #     for index, value in tfidf:
        #         row.append(i)
        #         col.append(index)
        #         data.append(value)
        #         #docs_vectors[i][index] = value
        # docs_vectors = csr_matrix((data, (row, col)), shape=(len(docs_bow), len(self.tfidf.idfs))).toarray()
        #docs_vectors_np = [numpy.array(doc) for doc in docs_vectors] 
        # docs_tfidf = self.tfidf[docs_bow]
        # docs_weights = [[x[1] for x in doc] for doc in docs_tfidf]
        #print(docs_weights)
        #docs_embeddings = self.embedding_model.encode(docs_formatted)
        #self.rag.add(ids=uuids, documents=docs_formatted, embeddings=docs_embeddings, metadatas=metadata_formatted)
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)

    def add_nav(self,nav_file):
        docs = self.load_docs(nav_file)
        docs_formatted, metadata_formatted = self.format_nav(docs)
        uuids = [str(uuid4()) for _ in range(len(docs_formatted))]
        # docs_tokenized = []
        # for doc in docs_formatted:
        #     self.tokenizer.process(doc)
        #     tokenized = [x.text for x in self.tokenizer]
        #     docs_tokenized.append(tokenized)
        # docs_bow = [self.dct.doc2bow(doc) for doc in docs_tokenized]
        # #docs_vectors = numpy.zeros((len(docs_bow),len(self.tfidf.idfs)), float)
        # row = []
        # col = []
        # data = []
        # for i,doc in enumerate(docs_bow):
        #     tfidf = self.tfidf[doc]
        #     for index, value in tfidf:
        #         row.append(i)
        #         col.append(index)
        #         data.append(value)
        #         #docs_vectors[i][index] = value
        # docs_vectors = csr_matrix((data, (row, col)), shape=(len(docs_bow), len(self.tfidf.idfs))).toarray()
        #docs_vectors_np = [numpy.array(doc) for doc in docs_vectors] 
        # docs_tfidf = self.tfidf[docs_bow]
        # docs_weights = [[x[1] for x in doc] for doc in docs_tfidf]
        # print(docs_weights)
        #docs_embeddings = self.embedding_model.encode(docs_formatted)
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)
        #self.rag.add(ids=uuids, documents=docs_formatted, embeddings=docs_vectors,metadatas=metadata_formatted)
        

    def prepare_instructions(self,instruction_file,name):
        instructions = self.load_lines(instruction_file)
        self.instructions[name] = self.clean_lines(instructions)

    def prepare_patterns(self,pattern_file):
        patterns = self.load_lines(pattern_file)
        self.patterns = self.clean_lines(patterns)

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

    def format_qa(self,domain,docs):
        rag_documents = []
        rag_metadata = []
        for doc in docs:
            content = doc.page_content
            # Remove BOM character if present
            cleaned_content = content.lstrip('\ufeff')
            # Split the content by ';' to extract Q&A parts
            parts = cleaned_content.split('\n')[0].split(';')
            inp = parts[2].replace('Context: ', '') # Extract actual question
            outp = parts[3]
            context = parts[4]
            meta = {'type':domain, 'answer': outp, 'step_context' : str(context)}
            rag_documents.append(inp)
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
            inp = parts[0].replace('Input: ', '').strip()  # Extract input command
            outp = parts[1].replace('Action: ', '').strip()  # Extract action
            meta = {'type':'nav', 'action':outp, 'step_context':'all'}
            rag_documents.append(inp)
            rag_metadata.append(meta)
        return rag_documents, rag_metadata
