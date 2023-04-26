import discord, random
from model import Chatbot, Preprocess
from characters import ChatGPT

# loading in ChatGPT details from characters module
character = ChatGPT()

intents = discord.Intents.all()
intents.members = False
intents.presences = False

client = discord.Client(intents=intents)
chatbot = Chatbot(
    tokenizer="PygmalionAI/pygmalion-350m",
    checkpoint="PygmalionAI/pygmalion-350m",
    device="cpu",
    persona=character["persona"],
    questions=character["questions"],
    responses=character["responses"],
    max_sequences=20,
)


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):

    if message.author == client.user:
        return

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
