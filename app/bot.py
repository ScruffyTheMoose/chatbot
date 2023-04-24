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
        print(user_message)

        # generate response from chatbot
        response = chatbot.input(user_message)
        print(response)

        # Do something with user_input_text here
        await message.channel.send(response)

        print("Response sent.")

    else:
        print("Something went wrong...")


if __name__ == "__main__":
    client.run(
        "MTA5MjI5OTkyMjQ5MTA0ODAyOA.Gpu4e8.Wq8EJrPtAgwQXiXGehx7-UxgTg91OoD3c4iVko"
    )


# bot token:
# MTA5MjI5OTkyMjQ5MTA0ODAyOA.Gpu4e8.Wq8EJrPtAgwQXiXGehx7-UxgTg91OoD3c4iVko
