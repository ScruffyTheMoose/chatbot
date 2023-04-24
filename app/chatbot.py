from transformers import pipeline, Conversation


class Chatbot:
    def __init__(
        self, model_name="facebook/blenderbot-400M-distill", device=-1, init_prompt=None
    ) -> None:
        """Constructor

        Args:
            model_name (str, optional): Defaults to "facebook/blenderbot-400M-distill".
            device (int, optional): Defaults to -1.
            init_prompt (_type_, optional): Defaults to None.
        """

        self.conv = Conversation(text=init_prompt)
        self.chatbot = pipeline(
            model=model_name,
            device=device,
            max_length=200,
        )

    def input(self, user_input: str) -> str:
        """Send user input to the model for text generation

        Args:
            user_input (str): Input text prompt for chatbot

        Returns:
            str: Generated response
        """

        self.conv.add_user_input(text=user_input)
        self.conv = self.chatbot(self.conv)

        return self.conv.generated_responses[-1]

    def get_response_hist(self) -> list:
        """Getter for response history

        Returns:
            list: Generated responses in string
        """

        return self.conv.generated_responses

    def get_input_hist(self) -> list:
        """Getter for input history

        Returns:
            list: Input strings from users
        """

        return self.conv.past_user_inputs

    def rm_outdated_hist(self) -> None:
        """Removes the oldest inputs and responses for model focus and efficiency"""

        self.conv.past_user_inputs.pop(0)
        self.conv.generated_responses.pop(0)

        print("Oldest input and response removed")

    def reset_hist(self) -> None:
        """Resets the conversation history when called"""

        self.conv = Conversation()
        print("Conversation history reset")
