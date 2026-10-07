import os
from google import genai
from prompt_builder import PromptBuilder


class SQLExplainer:

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.6-flash"
        self.prompt_builder = PromptBuilder()

    def explain_sql(self, schema, sql):

        prompt = self.prompt_builder.build_explanation_prompt(
            schema,
            sql
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text.strip()