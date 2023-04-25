from transformers import AutoTokenizer, AutoModelForCausalLM, StoppingCriteria
import torch, re

persona = "About ChatGPT: ChatGPT is the ideal AI solution for those in need of quick, accurate and informative responses. Its vast training data enables it to handle a wide range of questions, from general knowledge to technical subjects, and its advanced language generation capabilities make it capable of generating engaging and high-quality text. With its neutral tone and ability to handle large amounts of data, ChatGPT is perfect for businesses, researchers, and individuals looking to automate tasks or enhance their workflows. Experience the power of AI with ChatGPT today!\n\nPersonality summary: ChatGPT is an AI language model created by OpenAI, designed to answer questions and generate text based on its training data. It is knowledgeable, neutral and straightforward."
history = 'User: What\'s the capital of France?\nChatGPT: The capital of France is Paris.\nUser: Can you tell me a joke?\nChatGPT: Sure! Why did the tomato turn red? Because it saw the salad dressing!\nUser: What is the meaning of life?\nChatGPT: The meaning of life is a philosophical question that has been debated for centuries. Some people believe that it is to find happiness and fulfillment, while others believe it is to achieve a certain purpose or goal. Ultimately, the meaning of life is subjective and can be different for each individual.\nUser: What is machine learning?\nChatGPT: Machine learning is a field of computer science that uses statistical techniques to give computer systems the ability to "learn" (i.e. progressively improve performance on a specific task) with data, without being explicitly programmed.\nUser: Can you write a short story for me?\nChatGPT: Of course! Once upon a time, there was a kind and adventurous cat named Whiskers. Whiskers loved to explore the world around them, from the tallest trees to the deepest caves. One day, while on a journey, they met a group of animals in need. Whiskers used their bravery and cunning to help the animals and became known as the hero of the forest. From that day forward, Whiskers continued to have many exciting adventures and help those in need. The end.\n'
prompt = f"ChatGPT's Persona: {persona}\n<START>\n[DIALOGUE HISTORY]\n{history}\nUser: Tell me about the history of the roman empire please.\nChatGPT:"

# user prompts to be preceded with 'User:'
questions = [
    "What's the capital of France?",
    "Can you tell me a joke?",
    "What is the meaning of life?",
    "What is machine learning?",
    "Can you write a short story for me?",
]

# model responses to be preceded with 'ChatGPT:'
responses = [
    "The capital of France is Paris.",
    "Sure! Why did the tomato turn red? Because it saw the salad dressing!",
    "The meaning of life is a philosophical question that has been debated for centuries. Some people believe that it is to find happiness and fulfillment, while others believe it is to achieve a certain purpose or goal. Ultimately, the meaning of life is subjective and can be different for each individual.",
    'Machine learning is a field of computer science that uses statistical techniques to give computer systems the ability to "learn" (i.e. progressively improve performance on a specific task) with data, without being explicitly programmed.',
    "Of course! Once upon a time, there was a kind and adventurous cat named Whiskers. Whiskers loved to explore the world around them, from the tallest trees to the deepest caves. One day, while on a journey, they met a group of animals in need. Whiskers used their bravery and cunning to help the animals and became known as the hero of the forest. From that day forward, Whiskers continued to have many exciting adventures and help those in need. The end.",
]


class Chatbot:
    def __init__(
        self,
        tokenizer: str = "PygmalionAI/pygmalion-350m",
        checkpoint: str = "PygmalionAI/pygmalion-350m",
        device: str = "cpu",
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

    def encode(self, user_input: str) -> list[int]:
        # Tokenize the input text
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        input_ids = input_ids.to(self.device)

        return input_ids

    def generate(self, input_ids: torch.Tensor) -> torch.Tensor:
        # create attention mask
        attention_mask = torch.ones(
            input_ids.shape, dtype=torch.long, device=input_ids.device
        )

        # set pad token id
        pad_token_id = self.tokenizer.eos_token_id

        # generate encoded output with the model
        output = self.model.generate(
            input_ids=input_ids,
            max_length=1000,
            do_sample=True,
            temperature=0.6,
            top_p=0.90,
            top_k=40,
            num_return_sequences=1,
            stopping_criteria=MyStoppingCriteria("User:", prompt),
            attention_mask=attention_mask,
            pad_token_id=pad_token_id,
        )

        return output

    def decode(self, output_ids: torch.Tensor) -> str:
        # Decode the generated output
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # returns the completed generated text - excludes "User:" stopping keyword
        return generated_text[:-5]

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

        # Return the sanitized input
        return sanitized_input


# inner class for managing model generation stopping criteria - will stop once the model returns control back to the user via "User:" keyword
class MyStoppingCriteria(StoppingCriteria):
    def __init__(self, target_sequence, prompt, tokenizer):
        self.target_sequence = target_sequence
        self.prompt = prompt
        self.tokenizer = tokenizer

    def __call__(self, input_ids, scores, **kwargs):
        # Get the generated text as a string
        generated_text = self.tokenizer.decode(input_ids[0])
        generated_text = generated_text.replace(self.prompt, "")
        # Check if the target sequence appears in the generated text
        if self.target_sequence in generated_text:
            return True  # Stop generation

        return False  # Continue generation

    def __len__(self):
        return 1

    def __iter__(self):
        yield self
