from langchain_core import prompt_values
from fastapi import FastAPI, Request
from kubernetes import client, config
import os
import requests
from typing import TypedDict 
from langgraph.graph import StateGraph, END 
from langchain_openai import ChatOpenAI 
from langchain_core.messages import HumanMessage
from datetime import datetime
import subprocess

app = FastAPI()

# Kubernetes ke andar run hone par
# Pod ki ServiceAccount credentials use karega
config.load_incluster_config()

v1 = client.CoreV1Api()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/YOUR/WEBHOOK/URL")

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    model="openai/gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY")
)

class AgentState(TypedDict):
    alert_name: str
    pod_logs: str
    diagnosis: str
    action: str 

def diagnose_node(state: AgentState):
    print("🧠 AI is diagnosing the issue...")
    prompt = f"""
    Kubernetes Alert: {state['alert_name']}
    Pod Logs: {state['pod_logs']}
    
    You are an AI Site Reliability Engineer. Diagnose the root cause of this failure based on the logs.
    Decide the remediation action. If the app is crashing due to a temporary error, choose RESTART. 
    If it looks like a bad deployment/code bug, choose ROLLBACK.
    
    Respond strictly in this format:
    DIAGNOSIS: <your short explanation>
    ACTION: <RESTART or ROLLBACK or NONE>
    """
    response = llm.invoke([HumanMessage(content=prompt)])

    diagnose = "Unknown issue"
    action = "NONE"

    for line in response.content.split('\n'):
        if line.startswith("DIAGNOSIS:"):
            diagnose = line.replace("DIAGNOSIS:", "").strip()
        elif line.startswith("ACTION:"):
            action = line.replace("ACTION:", "").strip()

    return {"diagnosis": diagnose, "action": action}


def remediate_node(state: AgentState):
    action = state['action']
    print(f"🛠 AI Action Decision: {action}")
    
    # K8s Apps API initialize kar rahe hain
    apps_v1 = client.AppsV1Api()
    
    if action == "RESTART":
        print("🔄 Executing Deployment Restart for sample-app...")
        try:
            now = datetime.datetime.utcnow().isoformat()
            body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": now
                            }
                        }
                    }
                }
            }
            # 'sample-app' deployment ko restart kar rahe hain
            apps_v1.patch_namespaced_deployment(name="sample-app", namespace="app", body=body)
            print("✅ Deployment restarted successfully!")
        except Exception as e:
            print(f"❌ Error restarting deployment: {e}")
            
    elif action == "ROLLBACK":
        print("⏪ Executing Helm Rollback for sample-app...")
        try:
            # subprocess se terminal command chalayenge: helm rollback sample-app 0 -n app
            # (0 means previous revision)
            result = subprocess.run(["helm", "rollback", "sample-app", "0", "-n", "app"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Helm rollback successful!")
                print(f"Helm Output: {result.stdout}")
            else:
                print(f"❌ Error executing helm rollback (code {result.returncode}): {result.stderr}")
        except Exception as e:
            print(f"❌ Exception executing helm rollback: {e}")
        
    return state


# --- BUILD GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("diagnose", diagnose_node)
workflow.add_node("remediate", remediate_node)
workflow.set_entry_point("diagnose")
workflow.add_edge("diagnose", "remediate")
workflow.add_edge("remediate", END)
ai_agent_graph = workflow.compile()


def send_slack_notification(message: str):
    if not SLACK_WEBHOOK_URL:
        print("Slack Webhook URL is not configured.")
        return

    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ Successfully sent message to Slack")
        else:
            print(f"❌ Failed to send Slack message: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"❌ Error sending to Slack: {e}")


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    print("🚨 ALERT RECEIVED:")
    print(data)

    alert_name = data.get("alerts", [{}])[0].get("labels", {}).get("alertname", "Unknown Alert")
    send_slack_notification(f"🚨 *Kubernetes Alert Received:* {alert_name}\n🧠 *AI Agent is collecting logs and diagnosing...*")
    
    # app namespace ke pods list karo aur logs collect karo
    pods = v1.list_namespaced_pod(namespace="app")
    all_logs = ""

    for pod in pods.items:
        pod_name = pod.metadata.name
        
        print(f"Pod: {pod_name}, Status: {pod.status.phase}")
        
        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace="app",
                tail_lines=20
            )
            print(f"Logs for {pod_name}:\n{logs}")
            all_logs += f"\n--- Logs for {pod_name} ---\n{logs}\n"
        except Exception as e:
            print(f"Could not read logs for {pod_name}: {e}")
            all_logs += f"\n--- Could not read logs for {pod_name}: {e} ---\n"
        
    # --- LANGGRAPH AI EXECUTION ---
    print("🚀 Triggering AI LangGraph Workflow...")
    inputs = {"alert_name": alert_name, "pod_logs": all_logs}
    result = ai_agent_graph.invoke(inputs)
    
    final_message = (
        f"✅ *AI Diagnosis Complete*\n"
        f"🔍 *Root Cause:* {result['diagnosis']}\n"
        f"🛠 *Action Taken:* {result['action']}"
    )
    send_slack_notification(final_message)
    # -------------------------------

    return {"status": "received", "diagnosis": result['diagnosis'], "action": result['action']}
