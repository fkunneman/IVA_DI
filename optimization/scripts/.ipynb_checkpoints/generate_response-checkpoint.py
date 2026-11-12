
import csv

class Turns:

    def __init__(self):
        self.turns = []
    
    def read_log(self,logfile):
        with open(logfile) as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            c = 0
            for row in csvreader:
                if c > 0:
                    rowdict = {'asr':row[0],'agent_response':row[12]}
                    rowdict['history'] = self.return_history()
                    self.turns.append(rowdict)
                c += 1

    def return_history(self):
        history = []
        for turn in self.turns:
            history.extend(['user: ' + turn['asr'],'agent: ' + turn['agent_response']])
        return history

    def return_turn(self,index):
        return self.rows[index]

class ResponseGenerator:

    def __init__(self,agent,model=False):
        self.agent = agent
        self.model = model
        self.response = None

    ### MODULES ###

    def generate_response(self, turn, threshold=0.20):
        output = self.agent.chat_with_agent(turn['asr'],threshold)
        return output
        
        
        
    
    def correct_asr(self,turns):
        system_prompt = '''Je werkt als expert in conversaties samen met spraakherkenning die gebruikt wordt in een spraakassistent. Je doel is om voor de output van de spraakherkenning in te schatten of het een correcte herkenning is van de spraak. Dit doe je op basis van de output zelf en het gesprek tot dan toe. Maak daarbij de inschatting of de output van de spraakherkenning passend of relevant is in het licht van de conversatie. Je corrigeert alleen output die erg onwaarschijnlijk is, en als je een correctie doet staat niet te ver af van de klank van wat de spraakherkenning nu teruggeeft. 'Wat hegje' kan niet gecorrigeerd worden als 'volgende stap'. 
        
        Extra context: het gaat om een spraakassistent die digitaal analfabeten helpt bij het navigeren van een website. Specifiek gaat het hier om het boeken van een afspraak bij de gemeente en het plannen van een reis met het OV. De gebruiker kan op ieder moment vragen stellen, en er zijn een paar standaard commando's, zoals 'ik wil starten', 'volgende', 'vorige', 'herhaal', 'klaar', 'start', 'wat zeg je?' en 'wat moet ik doen?'. 

        Als input krijg je steeds de gespreksgeschiedenis, gevolgd door de output van de spraakherkenning die daarop volgt. Deze zijn met komma's onderscheiden. Je voegt daaraan je oordeel toe als tuple, met daarin: ([output ASR],['passend' / 'niet passend'],[suggestie voor wat de gebruiker waarschijnlijk gezegd heeft])

        Twee voorbeelden:

        INPUT: {"History": ["User: 'Ik wil starten'", "Agent: 'Super! Stap 1. Scroll naar beneden. Klik op de blauwe tekst 'Paspoort, ID-kaart en rijbewijs'"],"ASR":"Bolgende"}
        OUTPUT: ("Bolgende","niet passend","Volgende")}
        INPUT: {"History": ["User: 'Ik wil starten', Agent: 'Super! De eerste stap: onder de woorden 'Waar wil je heen?' staat een tekstvakje. Type daar het station in waar vandaan je wil vertrekken.'"],"ASR":"Kun je dat nog een keer herhalen?"}
        OUTPUT: ("Kun je dat nog een keer herhalen?","passend","-")

        Beoordeel nu de volgende input, steeds onderscheiden door een nieuwe regel. Genereer je oordeel als tuple achter 'OUTPUT'. 
        '''
        prompt = system_prompt + self.retrieve_prompt_input_ASR(turns)
        print('PROMPT INPUT', prompt)
        output = self.model(prompt)        

        return output
        
        # request LLM to correct ASR output if it is unintelligable in the context of the conversation
        #agent_response = self.model.invoke(messages_for_llm, max_tokens=250)

    #def correct_response(self,history,asr_output,agent_response):
        # request LLM to correct the agent response if it is unintelligable in the context of the conversation
    #    continue
    
    #def apply_threshold(self):
        # run instruction agent and select response based on retrieval output
    #    continue


    ### Helpers #####
    def retrieve_prompt_input_ASR(self,turns):
        prompt_input = []
        for turn in turns[:3]:
            history = turn['history']
            asr = turn['asr']
            prompt_input.append("INPUT: {\"History\": " + str(history) + ", \"ASR\": " + str(asr) + "}")   
            prompt_input.append("OUTPUT:")
            prompt_input_str = '\n'.join(prompt_input)
        return prompt_input_str
            
    
 