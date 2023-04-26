import discord, random
from model import Chatbot, Preprocess
from characters import ChatGPT

# loading in ChatGPT details from characters module
character = ChatGPT()

# opening all intents except for privilaged
intents = discord.Intents.all()
intents.members = False
intents.presences = False

# instantiating discord client
client = discord.Client(intents=intents)

# instantiating chatbot
chatbot = Chatbot(
    tokenizer="PygmalionAI/pygmalion-350m",  # using the smallest PygmalionAI model for best CPU performance
    checkpoint="PygmalionAI/pygmalion-350m",
    device="cpu",  # selecting which device the model is computed on - can use code <"cuda" if torch.cuda.is_available() else "cpu"> or can explicitly select a device
    persona=character["persona"],  # persona from our selected character
    questions=character["questions"],  # questions list from our selected character
    responses=character["responses"],  # responses list from our selected character
    max_sequences=30,  # number of sequence pairs (question : response) that it will keep track of. The more memory available (RAM or VRAM), the more you can track.
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

    # chatbot responds only to messages beginning with key '~!'
    if message.content.startswith("~!"):

        # remove '~!' from start of message and sanitizes contents
        user_message = Preprocess.sanitize_input(message.content[2:])

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
