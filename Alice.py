from pathlib import Path
import os
from random import SystemRandom
import hashlib
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration 
from pubnub.pubnub import PubNub 
from pprint import pprint
import time

python_file_dir = os.getcwd() # Gets the Current Directory that this .py file is located in
TxID = 0 #Transaction ID
json_format = "{ \"TxID\": <TxID>, \"Hash\": \"<Hash>\", \"Nonce\": <Nonce>, \"Transaction\": <Transaction> }"
exclude = [] #Positions/Numbers to exclude as they've been called already
nonce = 0 #Alice's Nonce

#PubNub attributes
channel = "Channel-7mylwl3m4" #Publish and Sub Channel
pnconfig = PNConfiguration()
pnconfig.subscribe_key = "sub-c-42a99d3e-ba7c-11eb-99ea-662615fc053c"
pnconfig.publish_key = "pub-c-831aab7b-7557-41ea-9ae1-35b491957e85"
pnconfig.uuid = "Alice"
pubnub = PubNub(pnconfig)

def my_publish_callback(envelope, status):
    pass

def here_now_callback(result, status):
    bobisHere = False
    for channel_data in result.channels:
        for occupant in channel_data.occupants:
            if(occupant.uuid == "Bob" and TxID == 0):# Bob is here lets start
                generateGensisBlock("Alice") # Generate Gensis Block
                print("Created Gensis Block")
                generateTransaction("Alice") # Generate a transaction
                
                bobisHere = True
                break
        if(bobisHere == True):
            break

class MySubscribeCallback(SubscribeCallback):  
    def presence(self, pubnub, presence): #Activiated when a new UUID is connected
        print("presense",presence.uuid, presence.event)
        #Check occupants for bob
        if(TxID == 0): # Before we start make sure Bob is here
            BobisHere = pubnub.here_now()\
            .channels(channel)\
            .include_uuids(True)\
            .pn_async(here_now_callback)

    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        msg = message.message
        if type(msg) == dict:
            if msg['sender'] != pnconfig.uuid:
                print(str(TxID+1)+": Bob: ", msg['content'])
                #save incoming message
                processTransaction(msg['content'])
                #Send Operation
                if TxID < 9:
                    generateTransaction("Alice")
        if(TxID >= 9):
            unsub() #Exit program    
                  
            


def generateGensisBlock(person): # Generates Gensis Block
    #Creating Directory
    global TxID
    path_way = python_file_dir+"/"+person
    if Path(path_way).is_dir() == True:
        for file in os.listdir(Path(path_way)):
            temp = path_way+"/"+file
            os.remove(temp) #Deletes all files within Person folder
        os.rmdir(path_way) #Deletes directory if it exists
    # Creates directory 
    os.makedirs(path_way) 
    path_way += "/Block0.json"  

    #Creating Gensis Block
    gensis_block = "{ \"TxID\": 0, \"Hash\": \"This is the genesis block.\", \"Nonce\": 0, \"Transaction\": [] }"
    file_out = open(path_way,"w") # Creates gensis block if it doesn't exist
    file_out.write(gensis_block) # Write to file
    file_out.close() # Close Block0.json

def generateTransaction(person):
    global TxID
    global nonce  
    TxID +=1  
    temp_hash = getHash(person)
    next_block = json_format # Copies the formating of JSON
    Transaction = [person, str(randomNumber())] #<Transaction>
    next_block = next_block.replace('<TxID>',str(TxID))
    next_block = next_block.replace('<Hash>', str(temp_hash))
    next_block = next_block.replace('<Nonce>',str(nonce))
    next_block = next_block.replace('<Transaction>',str(Transaction))

    file_out = open(python_file_dir+"/"+person+"/Block"+str(TxID)+ ".json", "w")
    file_out.write(next_block)
    file_out.close()

    data = str(TxID)+";"+str(temp_hash)+";"+str(nonce)+";"+str(Transaction[1])
    send(data) #Send Message
    print(str(TxID)+": Alice: "+ data)

def processTransaction(data): #Validates JSON file & Stores it
    global TxID
    global exclude
    #Re-organise string
    separated_data = ['']*4 # 0 TxID; 1 Hash; 2 Nonce; 3 Transaction position
    tIndex = 0
    for char in data:
        if(char == ";"):
            tIndex += 1
        else:
            separated_data[tIndex] = separated_data[tIndex]+str(char)
    
    #---validate---
    valid = True
    file_in = open(python_file_dir+"/Alice/Block"+ str((TxID)) + ".json", "r") 
    previous_block = file_in.read() # Grabs previous block string format
    file_in.close()
    temp_hash = previous_block + str(separated_data[2]) #Adds Nonce to string block
    temp_hash = hashlib.sha256(temp_hash.encode())
    
    #Validate TxID
    if(int(separated_data[0]) != (TxID+1)):
        valid = False
        print("Error: Bob's Transaction number "+str(separated_data[0])+" is wrong!")
    
    #Validate Hash/Nonce
    if(str(separated_data[1]) != str(temp_hash.hexdigest())):
        valid = False
        print("Error: Bob's Hash/Nonce "+str(separated_data[1])+" doesn't match! "+str(temp_hash.hexdigest()))

    #Validate Transaction
    if(int(separated_data[3]) in exclude): 
        valid = False
        print("Error: Bob's choosen position "+str(separated_data[3])+" is already taken!")


    if valid:
        #---store---
        #Format
        next_block = json_format # Copies the formating of JSON
        Transaction = ["Bob", separated_data[3]] #<Transaction>
        next_block = next_block.replace('<TxID>',str(separated_data[0]))
        next_block = next_block.replace('<Hash>', str(separated_data[1]))
        next_block = next_block.replace('<Nonce>',str(separated_data[2]))
        next_block = next_block.replace('<Transaction>',str(Transaction))
        TxID = int(separated_data[0])
        exclude.append(int(separated_data[3])) # Add position to the exclude list
        
        #Write into text file
        file_out = open(python_file_dir+"/Alice/Block"+str(separated_data[0])+ ".json", "w")
        file_out.write(next_block)
        file_out.close()
    else:
        unsub() # Unsubscribe
        os._exit(-1)#Exit program

def randomNumber(): #Computes Random Number
    global exclude
    true_random = SystemRandom().randrange(1,10) # 1-9 (inclusive of 9)
    while true_random in exclude: #if in exclusion list find new random
        true_random = SystemRandom().randrange(1,10) # 1-9 (inclusive of 9)
    exclude.append(true_random)
    return true_random # When true random is found return it

def getHash(person): #Computes Hash
    temp_nonce = 0
    file_in = open(python_file_dir+"/"+person+"/Block"+ str((TxID-1)) + ".json", "r") 
    previous_block = file_in.read() # Grabs previous block string format
    file_in.close()

    temp_hash = previous_block + str(temp_nonce) #Adds Nonce to string block
    hashed_block = hashlib.sha256(temp_hash.encode()) # Turns String to Bytes Then hash
    while int(hashed_block.hexdigest(),16) >= 2**248:
        temp_nonce+=1 #incrementally increase by 1
        temp_hash = previous_block + str(temp_nonce) #Adds Nonce to string block
        hashed_block = hashlib.sha256(temp_hash.encode()) # Turns String to Bytes Then hash

    setNonce(temp_nonce) #Once found the nonce set it
    return hashed_block.hexdigest()
 
def setNonce(temp_nonce): #Updates Nonce
    global nonce
    nonce = temp_nonce


def send(data): 
    pubnub.publish()\
        .channel(channel).message({"sender": pnconfig.uuid, "content": data})\
        .pn_async(my_publish_callback)
    
def unsub():
    pubnub.unsubscribe()\
        .channels(channel)\
        .execute()     
              
pubnub.add_listener(MySubscribeCallback())

pubnub.subscribe()\
    .channels(channel)\
    .with_presence()\
    .execute()


