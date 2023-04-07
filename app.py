import os
import logging
from emergent.agent import ChatAgent, HierarchicalMemory
import emergent
from openai.embeddings_utils import get_embedding
from flask import Flask, render_template, request, jsonify
from functools import partial
import openai
import atexit


os.environ["OPENAI_API_KEY"] = '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'


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
memory_path = "./memories.json"

try:
    memory = HierarchicalMemory.from_json(memory_path)
    logging.info(f"Loaded memories from {memory_path}")
except:
    logging.info(f"No {memory_path} file found, initializing new database")
    memory = HierarchicalMemory(model="gpt-3.5-turbo")

memory.model = "gpt-3.5-turbo"


@emergent.tool()
def search_memory(query):
    """Search through your own memories using this tool."""
    return memory.query(query).content


agent = ChatAgent(memory=memory, tools=[search_memory], model="gpt-4")
agent.memory.logs = []


def save_upon_exit(agent, memory_path):
    try:
        agent.end_conversation(memory_path)
    except:
        print("Could not save!")

atexit.register(partial(save_upon_exit, agent, memory_path))


app = Flask(__name__)
app.static_folder = 'static'

@app.route('/')
def home():
    return render_template('index.html')

def handle_ai_interaction(user_input):
    response = ""
    try:
        print(f"User input: {user_input}")  # Debugging line
        response_generator = agent.send(user_input)
        
        for r in response_generator:
            if isinstance(r, dict) and "tool_result" in r:
                response += r["tool_result"] + '\n'
            elif isinstance(r, str):
                response += r
    except:
        logging.warning(f"Call failed")
        agent.end_conversation(memory_path)

    print(f"Response: {response}")  # Debugging line
    return response

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return handle_ai_interaction(userText)

@app.route('/save_and_exit', methods=['POST'])
def save_and_exit():
    try:
        agent.end_conversation(memory_path)
        os._exit(0)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
