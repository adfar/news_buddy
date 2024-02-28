from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from typing import Annotated

app = FastAPI()

# for fetch api. change allowed origins before deploying
app.add_middleware(CORSMiddleware, allow_origins=["*"])


@app.post("/summary")
async def summarize(url: Annotated[str, Form()]):
    """Returns a summary of 'url'"""
    loader = WebBaseLoader(url)
    docs = loader.load()
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo-preview")
    chain = load_summarize_chain(llm, chain_type="stuff")
    output = chain.invoke(docs)
    return output["output_text"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
