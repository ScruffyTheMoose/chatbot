import discord, torch
from model import Chatbot, Preprocess
import characters

# loading in ChatGPT details from characters module
character = characters.Barack_Obama()

# opening all intents except for privilaged
intents = discord.Intents.all()
intents.members = False
intents.presences = False

# instantiating discord client
client = discord.Client(intents=intents)

# instantiating chatbot
chatbot = Chatbot(
    tokenizer="PygmalionAI/pygmalion-1.3b",
    checkpoint="PygmalionAI/pygmalion-1.3b",
    device="cuda",  # selecting which device the model is computed on - can use code <"cuda" if torch.cuda.is_available() else "cpu"> or can explicitly select a device
    name=character["name"],
    persona=character["persona"],  # persona from our selected character
    questions=character["questions"],  # questions list from our selected character
    responses=character["responses"],  # responses list from our selected character
    max_sequences=10,  # number of sequence pairs (question : response) that it will keep track of. This includes what is imported from the characters module. The more memory available (RAM or VRAM depending on device), the more you can track.
)


@client.event
async def on_ready():
    # chatbot is now ready for inputs
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):

    # chatbot will not respond to itself
    if message.author == client.user:
        return

    # chatbot responds only to messages beginning with key '!'
    if message.content.startswith("!"):

        # remove '~!' from start of message and sanitizes contents
        user_message = Preprocess.sanitize_input(message.content[1:])

        # confirming input recieved correctly
        print(f"User: {user_message}")

        # generate response from chatbot
        response = chatbot.run(input=user_message)

        # confirming response sent correctly
        print(f"Bot: {response}")

        # Do something with user_input_text here
        await message.channel.send(response)


# I pushed an old key alright don't judge me
# now i gotta do this thing with the thingy
key = open("key.pw", "r").read()

if __name__ == "__main__":
    client.run(key)
