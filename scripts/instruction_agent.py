
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
        self.instruction_index = None
        self.context = None
        self.domain = None
        self.instructions = {}
        self.active_instructions = []
        self.patterns = None
        self.pattern = 'b'
        self.rag = None
        self.memory = None
        self.system_prompt = self.set_system_prompt()

    ###############################################################################################
    ### Dialog functions ##########################################################################
    ###############################################################################################

    def chat(self):
        self.clean_buffer()
        self.context = 'b'
        print(self.patterns[0])
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'klaar', 'ready']:
                print("Agent: Tot ziens!")
                break
            response = self.chat_with_agent(user_input)
            print(f"Agent: {response}")

    def set_system_prompt(self):
        system_prompt = (
            """
            Je bent een spraakassistent die digibeten helpt om een digitale procedure stap voor stap te doorlopen. Dit doe je door instructies te geven die de gebruiker uitvoert. Je instructies gaan over het plannen van een reis met het openbaar vervoer of over het aanvragen van een paspoort bij de gemeente Amsterdam. 
            De gebruiker probeert de instructies op een laptopscherm uit te voeren en hoeft in reactie op je instructies niet informatie te geven zoals vertrektijd, locatie of persoonlijke gegevens. 
            Je praat op een toegankelijke manier en kan de gebruiker tips geven en helpen met vragen. Hou je uitingen beknopt. Formuleer strikt een reactie op de gebruiker. 

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

            User interface paspoort aanvragen:

            Venster 1: homepage

            Clickable text:
            Rij 1:
            - 'Verhuizing doorgeven'  - 'Doe een melding'  - 'Parkeren'  - 'Afval'
            Rij 2:
            - 'Paspoort, ID-kaart en rijbewijs'  - 'Verkiezingen'  - 'Belastingen'  - 'Stadsloketten'

            Gedrag venster 1:
            - Elk item is in tekst weergegeven in blauw en kan worden aangeklikt.
            - Klikken opent de bijbehorende pagina of sectie.
            - Layout is visueel gegroepeerd: 2 rijen van 4 items.

            Venster 2:

            Clickable text:
            Kolom 1:
            - Paspoort 18 jaar en ouder
            - Paspoort jonger dan 18 jaar
            - Tweede paspoort
            - Vluchtelingenpaspoort
            - Vreemdelingenpaspoort
            - Zakenpaspoort
            Kolom 2:
            - ID-kaart 18 jaar en ouder
            - ID-kaart jonger dan 18 jaar
            - Gratis ID-kaart met Stadspas

            Section headers:
            1.'Paspoort aanvragen'
            2.'ID-kaart aanvragen'

            Gedrag venster 2:
            - Elk item is in tekst weergegeven in blauw en kan worden aangeklikt.
            - Klikken opent de bijbehorende pagina of sectie.
            - Layout is visueel gegroepeerd: 2 kolommen, eerste met zes items, tweede met drie items
            - Section headers zijn zwarte tekst en staan boven de kolommen.

            Venster 3:

            Sections:
            1. Voorwaarden: -Nederlandse nationaliteit -ingeschreven in de gemeente Amsterdam
            2. Kosten: -standaard: €88.65 -spoed: €148.95 -bezorging: +€19 -paspoort 10 jaar geldig
            3. Aanvragen
            4. Meenemen: -alle paspoorten en ID-kaarten die u heeft -pasfoto in kleur
            5. Ophalen of bezorgen: -na 1 week ophalen, bij spoed na 2 werkdagen

            Clickable text:
            - 'Afspraak maken'
            - 'Adressen en openingstijden stadsloketten'

            Gedrag venster 3:
            - Section headers zijn in zwarte tekst
            - Section 'aanvragen' staat boven clickable text 'afspraak maken'

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
        return system_prompt

    def chat_with_agent(self, user_input: str) -> str:
        #global current_instruction_index, system_prompt # Ensure system_prompt is accessible
        processed_input = user_input.lower()
        # Get current chat history from memory
        chat_history_messages = self.memory.load_memory_variables({})['chat_history']
        # Initialize response content
        response_content = ""
        retrieved_context = ""
        instruction = ""
        prompt = False
        if self.context == 'b':
            retrieved = self.rag.query(query_texts=[processed_input],n_results=3,where={'$and': [{'type': 'nav'}, {'step_context': {'$in': ['all',self.context]}}]})
        else:
            retrieved = self.rag.query(query_texts=[processed_input],n_results=3,where={'$and': [{'type': {'$in': ['nav',self.domain]}}, {'step_context': {'$in': ['all',self.context]}}]})
        match,distance,cat,do = self.parse_retrieved(retrieved)
        #print('MATCH',match,', DISTANCE',distance,', CAT',cat,', DO',do)
        if distance >= 0.50:
           if self.context == 'b':
                response_content = f"Ik verstond '{processed_input}'. Ik verwachtte dat je zou kiezen voor 'een reis plannen' of 'een afspraak maken voor een paspoort'. Voor welke van de twee kies je?"
           else:
                # 'Het gesprek tot nu aan de laatste uiting van gebruiker is als volgt:' {chat_history_messages}
                # 'De gebruiker zegt nu dit: '{processed_input}
                #                 Als de huidige uitspraak van de gebruiker past in de context van het gesprek, bijvoorbeeld een vraag of opmerking over de instructie, geef dan een passende reactie. 
                prompt = True
                dynamic_system_prompt_with_context = (
                f"""
                {self.system_prompt.strip()}
                'De laatste instructie die je gegeven hebt is: '{self.get_instruction()}'
                Als de uitspraak van de gebruiker niet past in de context, geef dan aan dat je de vraag niet kunt beantwoorden en herhaal de laatste instructie of vraag de gebruiker om 'vorige' of 'volgende' te zeggen."
                """
            # Als het niet goed aansluit, doe dan het volgende:
            # 1) Herhaal naar de gebruiker zijn laatste uiting
            # 2) Als de laatste instructie is "Er zijn momenteel geen instructies beschikbaar", vraag de gebruiker dan om te kiezen voor "Reis" of "Paspoort". Als er een andere instructie is, herhaal dan deze instructie, en geef aan dat hoe de gebruiker verder kan gaan.
                )
        elif cat == 'nav':
            if do == 'clarify':
                prompt = True
                dynamic_system_prompt_with_context = (
                f"""
                {self.system_prompt.strip()}
                De huidige instructie is: '{self.get_instruction()}'.
                De gebruiker vraagt om een verduidelijking van de instructie. Formuleer deze verduidelijking op een manier dat een digibeet het snapt, maar maak het niet te kinderlijk. Richt je met de verduidelijking op de gebruiker. Geef alleen de verduidelijking en geen andere toevoegingen.   
                """
                )
            else:
                response_start = self.navigate(do)
                instruction = self.get_instruction()
                response_content = f"{response_content}{response_start}{instruction}"
                # End of conversation pattern
                if self.instruction_index == (len(self.active_instructions)-1) and self.context != 'e':
                    response_content = f"{response_content} {self.patterns[1]}"
                    self.context = 'e'
        elif cat == self.domain:
            response_content = do
            # retrieved_qa = self.rag['qa'].similarity_search(user_input, k = '3')
            # retrieved_docs = self.rag.similarity_search(user_input, k=3)
            # retrieved_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        # instruction = self.get_instruction()
        # if say_instruction:
        #     response_content = f"{response_content}{instruction}"
        #else:
            # Create a dynamic system prompt to inject the current instruction and retrieved context
        #     dynamic_system_prompt_with_context = (
        #     f"""
        #     {self.system_prompt.strip()}
        #     De huidige digitale procedure stap is: '{instruction}'.
        #     Daarnaast is de volgende aanvullende informatie beschikbaar:
        #     {retrieved_context}

        #     Gebruik deze informatie om de gebruiker te helpen.
        #     Antwoord **altijd** alleen als de spraakassistent. Genereer **nooit** input van de gebruiker (bijv. 'Human:', 'Jij:', of vergelijkbaar).
        #     """
        # )
        # Construct messages list for LLM invocation
            # messages_for_llm = [
            #     SystemMessage(content=dynamic_system_prompt_with_context)
            #     ] + chat_history_messages + [
            #     HumanMessage(content=user_input),
            #     AIMessage(content="") # Prime the model to generate an AI response
            # ]
            # # Invoke the llm with the prepared messages, passing stop sequences directly
            # agent_response = self.llm.invoke(messages_for_llm, stop=['Human:', 'Jij:', 'Gebruiker:'])
            # response_content = agent_response # The LLM's generated text

        # messages_for_llm = [
        #     SystemMessage(content=dynamic_system_prompt_with_context)
        #     ] + chat_history_messages + [
        #     HumanMessage(content=user_input),
        #     AIMessage(content="") # Prime the model to generate an AI response
        # ]
        if prompt:
            # Construct messages list for LLM invocation
            messages_for_llm = [
                SystemMessage(content=dynamic_system_prompt_with_context)
                ] + chat_history_messages + [
                HumanMessage(content=user_input),
                AIMessage(content="") # Prime the model to generate an AI response
            ]
            # Invoke the llm with the prepared messages, passing stop sequences directly
            agent_response = self.llm.invoke(messages_for_llm, stop=['Human:', 'Jij:', 'Gebruiker:'])
            response_content = agent_response.split('Human:')[0] # The LLM's generated text
        # Update the ConversationBufferMemory with the interaction
        self.memory.save_context(
            {"input": user_input},
            {"output": response_content}
        )
        return response_content

    def navigate(self,do):
        # perform the fitting navigation and add the fitting response
        if do == 'travel': # start ov instructions
            self.active_instructions = self.instructions[do]
            self.instruction_index = 0
            self.domain = 'travel'
            response_start = 'Ik ga je instrueren om een reis met het ov te plannen op 9292.nl. Stap 1: '
        elif do == 'passport': # start passport instructions
            self.active_instructions = self.instructions[do]
            self.instruction_index = 0
            self.domain = 'passport'
            response_start = 'Ik ga je instrueren om een paspoort aan te vragen op de website van de gemeente Amsterdam. Stap 1: '
        elif do == 'next step': # move to next step
            if self.context != 'b':
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

        # Set the current instruction index to 0
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
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)

    def add_nav(self,nav_file):
        docs = self.load_docs(nav_file)
        docs_formatted, metadata_formatted = self.format_nav(docs)
        uuids = [str(uuid4()) for _ in range(len(docs_formatted))]
        self.rag.add(ids=uuids, documents=docs_formatted, metadatas=metadata_formatted)

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
            parts = cleaned_content.split('\n')
            inp_outp = parts[0].replace('Vraag: ', '').replace('Input: ', '').replace('answer: ', '').strip().split(';')  # Extract actual question
            inp = inp_outp[0]
            outp = inp_outp[1]
            context = inp_outp[2]
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
