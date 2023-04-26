from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    StoppingCriteria,
)
import torch, re, time


class Chatbot:
    def __init__(
        self,
        tokenizer: str = "PygmalionAI/pygmalion-1.3b",
        checkpoint: str = "PygmalionAI/pygmalion-1.3b",
        device: str = "cuda",
        name: str = "",
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
            name=name,
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

        t0 = time.time()

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

        # compute timing
        t1 = time.time()
        print(f"Compute time: {t1 - t0}")

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
        for q, r in zip(self.character.get_questions(), self.character.get_responses()):
            # append formatted question
            history += f"You: {q}\n"
            # append formatted response
            history += f"{self.character.get_name()}: {r}\n"

        complete_input = f"{self.character.get_name()}'s Persona: {self.character.get_persona()}\n<START>\n[DIALOGUE HISTORY]\n{history}\nUser: {user_input}\n{self.character.get_name()}:"

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
            max_length=5000,
            do_sample=True,
            temperature=0.7,
            top_p=0.85,
            top_k=40,
            num_return_sequences=1,
            stopping_criteria=GenStoppingCriteria(
                target_sequences=[
                    "You:",
                    "User:",
                ],  # keywords that are looked for to stop the model from generating - if unchecked, model will produce its own dialogue stream by talking to itself
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
        name: str = "",
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

        self.name = name
        self.persona = persona
        self.questions = questions
        self.responses = responses
        self.max_seq = max_sequences
        self.init_len = len(questions)

    def get_name(self) -> str:
        return self.name

    def get_persona(self) -> str:
        return self.persona

    def get_questions(self) -> list:
        return self.questions

    def append_questions(self, new_input: str) -> None:
        split_input = new_input.split(" ")
        trunc_input = " ".join(
            split_input[:20]
        )  # truncating stored inputs to preserve memory and maintain similar sized tensors between input and output

        self.questions.append(trunc_input)

        if len(self.questions) > self.max_seq:
            self.questions.pop(self.init_len)

    def get_responses(self) -> list:
        return self.responses

    def append_responses(self, new_output) -> None:
        split_output = new_output.split(" ")
        trunc_output = " ".join(
            split_output[:20]
        )  # truncating stored outputs for reason mentioned above

        self.responses.append(trunc_output)

        if len(self.responses) > self.max_seq:
            self.responses.pop(self.init_len)


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
    def __init__(
        self, target_sequences: list[str], complete_input: str, tokenizer: AutoTokenizer
    ) -> None:
        self.target_sequences = target_sequences
        self.complete_input = complete_input
        self.tokenizer = tokenizer

    # Currently, we decode the generated response each iteration to check for our stopping keywords
    # Alternatively, we could parse the encoded complete input out of the encoded generated response each iteration and then check for keyword tokens
    # The alt option would likely be faster (no encoding/decoding), but compute times are acceptable atm and I doubt we'll see significant improvement
    def __call__(self, input_ids, scores, **kwargs) -> None:

        # Get the generated text as a string
        generated_text = self.tokenizer.decode(input_ids[0])

        # excluding the initial complete input to prevent collisions with "User:" keyword
        generated_text = generated_text.replace(self.complete_input, "")

        # Check if the target sequence appears in the generated text
        for target in self.target_sequences:
            if target in generated_text:
                return True  # Stop generation

        return False  # Continue generation

    def __len__(self):
        return 1

    def __iter__(self):
        yield self
