import discord, random
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

    if message.content.startswith("~!") or random.randint(0, 100) < 10:

        # remove '~!' from start of message
        if message.content.startswith("~!"):
            user_message = message.content[2:]
        else:
            user_message = message.content

        # confirming input recieved correctly
        print(f"User: {user_message}")

        # allows any user to clear the chat history
        if user_message == "RESET":
            chatbot.reset_hist()
            return

        # generate response from chatbot
        response = chatbot.input_to_response(user_input=user_message)

        # confirming response sent correctly
        print(f"Bot: {response}")

        # Do something with user_input_text here
        await message.channel.send(response)

    # tracks contextual messages being sent in the chat
    else:
        user_message = message.content
        chatbot.add_input(user_input=user_message)

        # confirming input tracked
        print(f"Tracked: {user_message}")

    # clearing oldest input
    if len(chatbot.get_input_hist()) > 10:
        chatbot.rm_oldest_input()

    # clearing oldest response
    if len(chatbot.get_response_hist()) > 10:
        chatbot.rm_oldest_response()


# I pushed an old key alright don't judge me
key = open("key.pw", "r").read()

if __name__ == "__main__":
    client.run(key)
