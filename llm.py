from langchain_ollama import OllamaLLM

class LLMClient:

    def __init__(self,model):
        self.llm = OllamaLLM(model=model,temperature=0.1)

    async def generate(self,prompt):
        return self.llm.invoke(prompt)

    # async def generate(self,prompt):
    #     prompt = prompt.lower()
    #     if "complex" in prompt:
    #         return {
    #             "action": "DELEGATE",
    #             "children": 3,
    #             "roles": [
    #                 "Researcher",
    #                 "Analyst",
    #                 "Verifier"
    #             ],
    #             "subtasks": [
    #                 "Research Part",
    #                 "Analysis Part",
    #                 "Verification Part"
    #             ]
    #         }

    #     return {
    #         "action": "COMPLETE"
    #     }

class PromptBuilder:

    def build(self,role,sop,task,memory,rag):
        return f"""Role:{role}SOP:{sop}Task:{task}Memory:{memory}RAG:{rag}"""