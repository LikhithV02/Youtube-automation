import os
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAI
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
os.environ["LANGSMITH_TRACING"]="true"
os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"]="youtube-automation"

def web_search_agent(query: str):
    tavily_tool = TavilySearchResults(
        max_results=10,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=True,
        # include_domains=[...],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )

    tools = [tavily_tool]
    if "GROQ_API_KEY" in os.environ and os.environ["GROQ_API_KEY"]:
        model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)
    elif "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"]:
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)
    elif "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]:
        model = OpenAI(model="gpt-4o-mini", temperature=0.2)
    else:
        raise ValueError("No valid API key found for GROQ or GOOGLE.")


    # Initialize memory to persist state between graph runs
    checkpointer = MemorySaver()

    app = create_react_agent(model, tools, checkpointer=checkpointer)
    
    sys_prompt = '''You are an expert in web research. You must use the Tavily web research tool provided to you. Summarize all the websites researched and give the final response. This research is going to be used for a YouTube shorts script, so make sure to write in a way that is suitable for a YouTube video. Research on detailed visual description of the topic, as this will be used for generating AI imges for the video. Make sure to include a detailed description of the topic, and make it engaging for the audience.'''

    final_state = app.invoke(
        {"messages": [{"role": "user", "content": query}, {"role": "system", "content": sys_prompt}]},
        config={"configurable": {"thread_id": 42}}
    )
    return final_state["messages"][-1].content

if __name__ == "__main__":
    query = "Write origin story of Ironman"
    print(web_search_agent(query))