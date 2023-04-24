import discord
from chatbot import Chatbot

intents = discord.Intents.all()
intents.members = False
intents.presences = False

client = discord.Client(intents=intents)
chatbot = Chatbot()


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.content.startswith("~!"):

        print(f"Message recieved: {message.content}")

        # remove '~!' from start of message
        user_message = message.content[2:]

        # allows any user to clear the chat history
        if user_message == "RESET":
            chatbot.reset_hist()
            return

        print(user_message)

        # generate response from chatbot
        response = chatbot.input(user_message)
        print(response)

        # Do something with user_input_text here
        await message.channel.send(response)

        print("Response sent.")


# I pushed an old key alright don't judge me
key = open("key.pw", "r").read()

if __name__ == "__main__":
    client.run(key)
