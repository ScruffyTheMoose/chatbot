from transformers import AutoTokenizer, AutoModelForCausalLM, StoppingCriteria
import torch, re

# persona to be given to model
persona = "About ChatGPT: ChatGPT is the ideal AI solution for those in need of quick, accurate and informative responses. Its vast training data enables it to handle a wide range of questions, from general knowledge to technical subjects, and its advanced language generation capabilities make it capable of generating engaging and high-quality text. With its neutral tone and ability to handle large amounts of data, ChatGPT is perfect for businesses, researchers, and individuals looking to automate tasks or enhance their workflows. Experience the power of AI with ChatGPT today!\n\nPersonality summary: ChatGPT is an AI language model created by OpenAI, designed to answer questions and generate text based on its training data. It is knowledgeable, neutral and straightforward."

# user prompts to be preceded with 'User:'
questions = [
    "What's the capital of France?",
    "Can you tell me a joke?",
    "What is the meaning of life?",
    "What is machine learning?",
]

# model responses to be preceded with 'ChatGPT:'
responses = [
    "The capital of France is Paris.",
    "Sure! Why did the tomato turn red? Because it saw the salad dressing!",
    "The meaning of life is a philosophical question that has been debated for centuries. Some people believe that it is to find happiness and fulfillment, while others believe it is to achieve a certain purpose or goal. Ultimately, the meaning of life is subjective and can be different for each individual.",
    'Machine learning is a field of computer science that uses statistical techniques to give computer systems the ability to "learn" (i.e. progressively improve performance on a specific task) with data, without being explicitly programmed.',
]


class Chatbot:
    def __init__(
        self,
        tokenizer: str = "PygmalionAI/pygmalion-1.3b",
        checkpoint: str = "PygmalionAI/pygmalion-1.3b",
        device: str = "cuda",
        persona: str = "",
        questions: list = [],
        responses: list = [],
        max_sequences: int = 5,
    ) -> None:
        """Constructor

        Args:
            tokenizer (str, optional): Checkpoint name from pretrained huggingface models. Defaults to "PygmalionAI/pygmalion-350m".
            checkpoint (str, optional): Checkpoint name from pretrained huggingface models. Defaults to "PygmalionAI/pygmalion-350m".
            device (str, optional): Used to select device for compute - use "cuda" if enabled. Defaults to "cpu".
        """

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        self.model = AutoModelForCausalLM.from_pretrained(checkpoint)
        self.model.to(device)
        self.device = device

        # tracking raw version of last input for both StoppingCriteria and cleaning the response from the model
        self.complete_input = ""

        # implementing character class
        self.character = Character(
            persona=persona,
            questions=questions,
            responses=responses,
            max_sequences=max_sequences,
        )

    def run(self, input: str) -> str:
        """Runs the model on a prompt given by the user.

        Args:
            input (str): User input text - Ex: 'What should I do for fun when travelling in Paris?'

        Returns:
            str: Generated response from model - Ex: 'Explore the streets of the city. Take in the sights and sounds of the city. If you like, you can even hire a guide to take you to places that you wouldn't normally go to.'
        """

        # build complete input
        complete_input = self.gen_input(user_input=input)
        # encode
        input_ids = self.encode(complete_input=complete_input)
        # generate
        output_ids = self.generate(input_ids=input_ids)
        # decode
        response = self.decode(output_ids=output_ids)

        self.character.append_questions(input)
        self.character.append_responses(response)

        return response

    def gen_input(self, user_input: str) -> str:
        """Builds the complete input to be passed to the model including persona, dialogue history, and the new user input.

        Args:
            user_input (str): String of text containing the user input

        Returns:
            str: Complete input ready to be encoded and passed to the model
        """

        # declaring string to build history
        history = ""

        # appending formatted dialogue into history
        for q, r in zip(questions, responses):
            # append formatted question
            history += f"You: {q}\n"
            # append formatted response
            history += f"ChatGPT: {r}\n"

        complete_input = f"ChatGPT's Persona: {persona}\n<START>\n[DIALOGUE HISTORY]\n{history}\nUser: {user_input}\nChatGPT:"

        self.complete_input = complete_input

        return complete_input

    def encode(self, complete_input: str) -> torch.Tensor:
        """Uses the selected tokenizer to encode the user input text.

        Args:
            complete_input (str): Combined persona, dialogue history, and user input to be processed by the model.

        Returns:
            torch.Tensor: A Tensor object containing the encoded version of the input text.
        """

        # Tokenize the input text
        input_ids = self.tokenizer.encode(complete_input, return_tensors="pt")
        input_ids = input_ids.to(self.device)

        return input_ids

    def generate(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Uses the selected model to process the encoded input.

        Args:
            input_ids (torch.Tensor): Encoded user input text.

        Returns:
            torch.Tensor: Encoded model output text.
        """

        # create attention mask
        attention_mask = torch.ones(
            input_ids.shape, dtype=torch.long, device=input_ids.device
        )

        # set pad token id
        pad_token_id = self.tokenizer.eos_token_id

        # generate encoded output with the model
        output_ids = self.model.generate(
            input_ids=input_ids,
            max_length=1000,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            num_return_sequences=1,
            stopping_criteria=GenStoppingCriteria(
                target_sequence="You:",
                complete_input=self.complete_input,
                tokenizer=self.tokenizer,
            ),
            attention_mask=attention_mask,
            pad_token_id=pad_token_id,
        )

        return output_ids

    def decode(self, output_ids: torch.Tensor) -> str:
        """Uses the selected tokenizer to decode the model output.

        Args:
            output_ids (torch.Tensor): Encoded model output text.

        Returns:
            str: A multi-line string containing the model output text.
        """

        # Decode the generated output
        generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        # returns the completed generated text - excludes "User:" stopping keyword and the initial complete input text
        return generated_text[:-5].replace(self.complete_input, "")


# class for managing character information
class Character:
    def __init__(
        self,
        persona: str = "",
        questions: list = [],
        responses: list = [],
        max_sequences: int = 5,
    ) -> None:
        """Constructor for character class.

        Args:
            persona (str, optional): A string containing any features or traits you want your character to embody. Defaults to "".
            questions (list, optional): _description_. Defaults to [].
            responses (list, optional): _description_. Defaults to [].
            max_sequences (int, optional): _description_. Defaults to 5.
        """

        if len(questions) != len(responses):
            raise ValueError("The number of questions and responses must be equal!")

        self.persona = persona
        self.questions = questions
        self.responses = responses
        self.max_seq = max_sequences

    def get_persona(self) -> str:
        return self.persona

    def get_questions(self) -> list:
        return self.questions

    def append_questions(self, new_input) -> None:
        self.questions.append(new_input)

        if len(self.questions) > self.max_seq:
            self.questions.pop(0)

    def get_responses(self) -> list:
        return self.responses

    def append_responses(self, new_output) -> None:
        self.responses.append(new_output)

        if len(self.responses) > self.max_seq:
            self.responses.pop(0)


# class for preprocessing input text from users
class Preprocess:
    def __init__(self) -> None:
        pass

    def sanitize_input(input_string: str) -> str:
        """Preprocessing method to sanitize user inputs with regex. Will automatically escape the following characters:
        - Backslash ()
        - Grave accent/backtick (`)
        - Asterisk (*)
        - Underscore (_)
        - Left curly brace ({)
        - Right curly brace (})
        - Left square bracket ([)
        - Right square bracket (])
        - Plus sign (+)
        - Hash/pound symbol (#)
        - Hyphen/minus sign (-)
        - Period/full stop (.)
        - Exclamation mark (!)
        - Left parenthesis/round bracket (()
        - Right parenthesis/round bracket ())
        - Vertical bar/pipe (|)
        - Dollar sign ($)
        - Ampersand (&)
        - At symbol (@)
        - Percent sign (%)
        - Less than symbol (<)
        - Greater than symbol (>)
        - Forward slash (/)
        - Question mark (?)

        Args:
            input_string (str): User prompt.

        Returns:
            str: Sanitized user prompt.
        """

        # Define a regular expression that matches punctuation and special characters
        special_chars = re.compile(r"([\\`*_{}\[\]+#\-.!()|\[\]{}$&@%<>/])")

        # Escape any special characters in the input
        sanitized_input = special_chars.sub(r"\\\1", input_string)

        return sanitized_input


# class for managing model generation stopping criteria - will stop once the model returns control back to the user via "User:" keyword
class GenStoppingCriteria(StoppingCriteria):
    def __init__(self, target_sequence, complete_input, tokenizer):
        self.target_sequence = target_sequence
        self.complete_input = complete_input
        self.tokenizer = tokenizer

    def __call__(self, input_ids, scores, **kwargs):
        # Get the generated text as a string
        generated_text = self.tokenizer.decode(input_ids[0])

        # excluding the initial complete input to prevent collisions with "User:" keyword
        generated_text = generated_text.replace(self.complete_input, "")

        # Check if the target sequence appears in the generated text
        if self.target_sequence in generated_text:
            return True  # Stop generation

        return False  # Continue generation

    def __len__(self):
        return 1

    def __iter__(self):
        yield self
