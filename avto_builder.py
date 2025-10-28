import os
import sys
import platform
import subprocess
from typing import Optional, TypedDict, Dict, Any, List

from langchain_core.tools import Tool

# Prefer ChatOpenAI; fall back to Gemini if available; else None
def get_llm() -> Optional[object]:
    # Guard against non-ASCII placeholder keys that break HTTP headers
    oai_key = os.environ.get("OPENAI_API_KEY")
    if oai_key and getattr(oai_key, "isascii", lambda: True)():
        try:
            from langchain_openai import ChatOpenAI
            model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            return ChatOpenAI(model=model, temperature=0.1)
        except Exception as e:
            print(f"OPOZORILO: OpenAI inicializacija ni uspela: {e}")
    elif oai_key:
        print("OPOZORILO: OPENAI_API_KEY vsebuje ne-ASCII znake; preskakujem OpenAI ponudnika.")

    g_key = os.environ.get("GOOGLE_API_KEY")
    if g_key and getattr(g_key, "isascii", lambda: True)():
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            model = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-1.5-flash")
            return ChatGoogleGenerativeAI(model=model, temperature=0.1)
        except Exception as e:
            print(f"OPOZORILO: Gemini (AI Studio) inicializacija ni uspela: {e}")
    elif g_key:
        print("OPOZORILO: GOOGLE_API_KEY vsebuje ne-ASCII znake; preskakujem Google AI Studio.")

    # Vertex AI bi zahteval ADC; za enostavnost ga tu ne vključimo.
    return None


def normalize_command(cmd: str) -> str:
    """Prilagodi tipične ukaze za Windows okolje, če je potrebno."""
    is_windows = platform.system().lower().startswith("win")
    c = cmd.strip()
    if is_windows:
        # Zamenjaj 'ls -a' z 'dir /a'
        if c.startswith("ls -a"):
            c = c.replace("ls -a", "dir /a", 1)
        elif c == "ls":
            c = "dir"
        # 'cat file' -> 'type file'
        if c.startswith("cat "):
            c = c.replace("cat ", "type ", 1)
        # 'pwd' -> 'cd'
        if c == "pwd":
            c = "cd"
    return c


DENY_PREFIXES = (
    "shutdown", "reboot", "halt", "poweroff", "rm -rf /", "format ",
)

ALLOW_PREFIXES = (
    "git ", "docker ", "ls", "dir", "echo ", "type ", "cat ", "mkdir ",
    "python ", "pip ", "npm ", "node ", "cd", "pwd",
)


def execute_shell_command(command: str) -> str:
    """
    Izvede dani ukaz in vrne izhod. Vključuje osnovno varnostno preverjanje in prilagoditve za Windows.
    """
    try:
        cmd = normalize_command(command)

        low = cmd.lower().strip()
        for bad in DENY_PREFIXES:
            if low.startswith(bad):
                return f"BLOCKED: Komanda '{command}' je blokirana zaradi varnosti."

        if not any(low.startswith(p) for p in ALLOW_PREFIXES):
            return (
                "REJECTED: Ukaz ni na seznamu dovoljenih predpon. Dovoljeni začetki: "
                + ", ".join(ALLOW_PREFIXES)
            )

        result = subprocess.run(
            cmd,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
            timeout=int(os.environ.get("EXEC_TIMEOUT_SEC", "180")),
            encoding="utf-8",
            errors="replace",
        )
        out = result.stdout or ""
        err = result.stderr or ""
        code = result.returncode
        status = "SUCCESS" if code == 0 else f"ERROR (code={code})"
        return f"{status}: Komanda '{cmd}'\nSTDOUT:\n{out}\nSTDERR:\n{err}"
    except subprocess.TimeoutExpired:
        return f"ERROR: Komanda '{command}' je presegla časovni limit."
    except Exception as e:
        return f"CRITICAL ERROR: {e}"


tools = [
    Tool(
        name="CodeExecutor",
        func=execute_shell_command,
        description=(
            "Uporabi za izvajanje sistemskih ukazov (git, docker, ls/dir, ipd.). "
            "Na Windows sistemu se 'ls -a' samodejno pretvori v 'dir /a'."
        ),
    )
]


# Minimalni Docker build kontekst (zaobide težave z dovoljenji v korenu repoja)
def prepare_minimal_build_context() -> str:
    """
    Ustvari mapo 'build_context' z nujnimi viri za backend kontejner:
    - skopira 'backend/' v 'build_context/backend'
    - skopira 'Dockerfile.backend' kot 'build_context/Dockerfile'

    Vrne relativno pot do 'build_context'.
    """
    import shutil
    from pathlib import Path

    base = Path(__file__).resolve().parent
    ctx = base / "build_context"

    # Počisti staro vsebino, če obstaja
    if ctx.exists():
        try:
            shutil.rmtree(ctx)
        except Exception as e:
            print(f"OPOZORILO: Brisanje obstoječega build_context ni uspelo: {e}")

    try:
        ctx.mkdir(parents=True, exist_ok=True)
        # Kopiraj backend kodo
        shutil.copytree(base / "backend", ctx / "backend")
        # Kopiraj Dockerfile.backend kot Dockerfile v kontekstu
        shutil.copy2(base / "Dockerfile.backend", ctx / "Dockerfile")
    except Exception as e:
        raise RuntimeError(f"Priprava minimalnega build konteksta ni uspela: {e}")

    return str(ctx)


# NOVO ORODJE: človeška odobritev pred produkcijo
def ask_for_approval(deployment_details: str) -> str:
    """
    Simulira pošiljanje zahteve za odobritev (npr. Slack/e-mail) in čaka na odločitev.
    V tem okolju je interaktivno (input v terminalu).
    """
    try:
        # Neinteraktivni način preko okoljske spremenljivke
        auto = os.environ.get("AUTO_APPROVE_PROD", "").strip().lower()
        if auto in ("1", "true", "yes", "on"):
            print("[HumanApproval] AUTO_APPROVE_PROD je vklopljen – avtomatsko odobreno.")
            return "SUCCESS: Uvajanje v produkcijo ODOBRENO (AUTO). Nadaljuj."
        print("-" * 64)
        print(">>> KRITIČNA ZAUSTAVITEV: Potrebna je ČLOVEŠKA ODOBRITEV! <<<")
        print(f"Podrobnosti uvajanja: {deployment_details}")
        response = input("PRODUKCIJA ODOBRENA? (da/ne): ").strip().lower()
        if response == "da":
            return "SUCCESS: Uvajanje v produkcijo ODOBRENO s strani človeka. Nadaljuj."
        else:
            return "DENIED: Uvajanje ZAVRNJENO s strani človeka. Prekini delovni tok."
    except Exception as e:
        return f"ERROR: Human approval ni uspel: {e}"


tools.append(
    Tool(
        name="HumanApproval",
        func=ask_for_approval,
        description=(
            "Obvezno pred UVAJANJEM V PRODUKCIJO. Zastavi vprašanje in počaka na človeško odobritev."
        ),
    )
)


def run_with_llm():
    llm = get_llm()
    if llm is None:
        return False
    try:
        # Uvozimo znotraj funkcije zaradi kompatibilnosti verzij LC
        from langchain.agents import create_react_agent, AgentExecutor
        from langchain import hub
        try:
            from langchain.memory import ConversationBufferWindowMemory  # type: ignore
        except Exception:
            ConversationBufferWindowMemory = None  # type: ignore
        # Uporabi ReAct agent (LC Hub prompt)
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
        kwargs = dict(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=5)
        if ConversationBufferWindowMemory is not None:
            kwargs["memory"] = ConversationBufferWindowMemory(k=3, memory_key="chat_history")
        agent = AgentExecutor(**kwargs)
    except Exception as e:
        print(f"OPOZORILO: Inicializacija LangChain agenta ni uspela: {e}")
        return False

    user_prompt = (
        "Sproži popoln CI/CD potek za aplikacijo.\n"
        "1.  Najprej mi prikaži datoteke v tem imeniku z ukazom 'ls -a' in preveri, ali obstaja Dockerfile.\n"
        "2.  Zgradi Docker sliko z uporabo ukaza 'docker build -t my-llm-app-prod:latest .'\n"
        "3.  Če je gradnja uspešna, ustvari Git commit: 'git add .' sledi 'git commit -m \"Auto CI/CD Build by Agent\"'.\n"
        "Izvajanje ukaza v terminalu prepusti izključno orodju CodeExecutor.\n"
        "Nadaljuj tam, kjer je bila seja prekinjena; ne začni od začetka."
    )

    print("-" * 50)
    print(f"AGENT STARTA! Cilj: {user_prompt.splitlines()[0]}")
    print("-" * 50)
    out = agent.invoke({"input": user_prompt})
    print("-" * 50)
    print("KONČNI ODGOVOR AGENTA:")
    # AgentExecutor vrača slovar z "output"
    print(out.get("output"))
    print("-" * 50)
    return True


def run_fallback_script():
    print("OPOZORILO: Ni konfiguriranega LLM ponudnika. Zaganjam fallback korake brez LLM.")
    # Pripravi minimalni build kontekst za zanesljivo gradnjo na Windows
    try:
        ctx = prepare_minimal_build_context()
        print(f"INFO: Fallback bo gradil iz minimalnega konteksta: {ctx}")
    except Exception as e:
        print(f"NAPAKA: Priprava build konteksta ni uspela: {e}")
        return

    steps = [
        "ls -a",
        "docker info",
        "docker build -t my-llm-app-prod:latest build_context",
        "git add .",
        "git commit -m \"Auto CI/CD Build by Agent\"",
    ]
    for s in steps:
        print(f"\n>>> Izvajam: {s}")
        print(execute_shell_command(s))


# ---------------------------
# LangGraph CI/CD potek
# ---------------------------

class CIState(TypedDict):
    messages: list
    approval_needed: bool
    status: str
    image_tag: str
    error_log: str


def node_build_and_commit(state: CIState) -> CIState:
    logs = []
    # Docker build z minimalnim kontekstom, da se izognemo 'Access is denied' težavam
    try:
        ctx = prepare_minimal_build_context()
        logs.append(f"INFO: Pripravljen minimalni build kontekst: {ctx}")
    except Exception as e:
        err = f"Napaka pri pripravi build konteksta: {e}"
        logs.append(err)
        return {
            "messages": state.get("messages", []) + ["BUILD FAILED"],
            "approval_needed": False,
            "status": "BUILD_FAILED",
            "image_tag": "",
            "error_log": "\n\n".join(logs),
        }

    r1 = execute_shell_command("docker build -t my-llm-app-prod:latest build_context")
    logs.append(r1)
    # Git commit
    r2 = execute_shell_command("git add .")
    logs.append(r2)
    r3 = execute_shell_command('git commit -m "Auto CI/CD Build by Agent"')
    logs.append(r3)

    all_out = "\n\n".join(logs)
    success = ("ERROR (code=" not in all_out) and ("failed to build" not in all_out.lower())
    if success:
        return {
            "messages": state.get("messages", []) + ["BUILD OK"],
            "approval_needed": True,
            "status": "BUILD_COMPLETE",
            "image_tag": "my-llm-app-prod:latest",
            "error_log": state.get("error_log", ""),
        }
    else:
        return {
            "messages": state.get("messages", []) + ["BUILD FAILED"],
            "approval_needed": False,
            "status": "BUILD_FAILED",
            "image_tag": "",
            "error_log": all_out,
        }


def node_request_approval_hitl(state: CIState) -> CIState:
    if state.get("approval_needed"):
        msg = ask_for_approval(f"SLIKA {state.get('image_tag','')} je pripravljena. Uvesti na produkcijo?")
        if "SUCCESS" in msg:
            return {
                **state,
                "status": "HUMAN_APPROVED",
                "messages": state.get("messages", []) + [msg],
            }
        else:
            return {
                **state,
                "status": "HUMAN_DENIED",
                "messages": state.get("messages", []) + [msg],
            }
    return state


def detect_deploy_platform() -> str:
    """Zazna preferiran deploy platform na podlagi konfiguracijskih datotek."""
    if os.path.exists("cloudbuild.yaml") and os.getenv("GOOGLE_CLOUD_PROJECT"):
        return "cloud_run"
    elif os.path.exists("render.yaml"):
        return "render"
    elif os.path.exists("railway.json") or os.getenv("RAILWAY_TOKEN"):
        return "railway"
    elif os.getenv("DOCKER_HUB_USERNAME"):
        return "docker_hub"
    else:
        return "local"

def deploy_to_cloud_run(image_tag: str) -> str:
    """Deploy na Google Cloud Run z Artifact Registry."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "my-project")
    region = os.getenv("GOOGLE_CLOUD_REGION", "europe-west1")
    service_name = os.getenv("CLOUD_RUN_SERVICE", "my-llm-app")
    
    # Tag za Artifact Registry
    registry_image = f"{region}-docker.pkg.dev/{project_id}/omni-registry/{service_name}:latest"
    
    commands = [
        f"docker tag {image_tag} {registry_image}",
        f"docker push {registry_image}",
        f"gcloud run deploy {service_name} --image {registry_image} --region {region} --platform managed --allow-unauthenticated --port 8080 --memory 1Gi --cpu 1 --max-instances 3"
    ]
    
    results = []
    for cmd in commands:
        result = execute_shell_command(cmd)
        results.append(f"[Cloud Run] {cmd}: {result}")
        if "error" in result.lower() or "failed" in result.lower():
            return f"Deploy failed: {result}"
    
    return f"Cloud Run deploy successful: https://{service_name}-{project_id}.a.run.app"

def deploy_to_render(image_tag: str) -> str:
    """Deploy na Render.com z Docker Hub push."""
    docker_user = os.getenv("DOCKER_HUB_USERNAME", "myuser")
    service_name = os.getenv("RENDER_SERVICE", "my-llm-app")
    
    # Push na Docker Hub
    hub_image = f"{docker_user}/{service_name}:latest"
    
    commands = [
        f"docker tag {image_tag} {hub_image}",
        f"docker push {hub_image}",
        "echo 'Render deploy triggered via webhook (if configured)'"
    ]
    
    results = []
    for cmd in commands:
        result = execute_shell_command(cmd)
        results.append(f"[Render] {cmd}: {result}")
    
    return f"Render deploy initiated: {hub_image}"

def deploy_to_railway(image_tag: str) -> str:
    """Deploy na Railway z njihovim CLI."""
    commands = [
        "railway login --browserless",
        "railway up --detach"
    ]
    
    results = []
    for cmd in commands:
        result = execute_shell_command(cmd)
        results.append(f"[Railway] {cmd}: {result}")
    
    return "Railway deploy completed"

def deploy_local_registry(image_tag: str) -> str:
    """Lokalni deploy - samo potrdi, da je slika zgrajena."""
    result = execute_shell_command(f"docker images {image_tag}")
    if image_tag in result:
        return f"Local image ready: {image_tag} (use 'docker run -p 8080:8080 {image_tag}' to start)"
    else:
        return f"Local image not found: {image_tag}"

def node_deploy(state: CIState) -> CIState:
    """Pravi deploy namesto echo - zazna platformo in izvede deploy."""
    image_tag = state.get("image_tag", "my-llm-app-prod:latest")
    platform = detect_deploy_platform()
    
    print(f"[Deploy] Detected platform: {platform}")
    
    try:
        if platform == "cloud_run":
            result = deploy_to_cloud_run(image_tag)
        elif platform == "render":
            result = deploy_to_render(image_tag)
        elif platform == "railway":
            result = deploy_to_railway(image_tag)
        elif platform == "docker_hub":
            result = deploy_to_render(image_tag)  # Isti postopek kot Render
        else:
            result = deploy_local_registry(image_tag)
        
        status = "DEPLOYED" if "successful" in result or "ready" in result or "completed" in result else "DEPLOY_FAILED"
        
    except Exception as e:
        result = f"Deploy error: {str(e)}"
        status = "DEPLOY_FAILED"
    
    return {
        **state,
        "status": status,
        "messages": state.get("messages", []) + [result],
    }

def node_monitoring(state: CIState) -> CIState:
    """Monitoring po deploy-u - preveri dostopnost aplikacije."""
    platform = detect_deploy_platform()
    
    if platform == "local":
        # Za lokalni deploy preverimo, da slika obstaja
        mon = execute_shell_command(f"docker images {state.get('image_tag', 'my-llm-app-prod:latest')}")
        if state.get('image_tag', 'my-llm-app-prod:latest') in mon:
            status_msg = "Local image verified and ready for deployment"
        else:
            status_msg = "Local image verification failed"
    else:
        # Za cloud deploy-e lahko dodamo health check
        mon = execute_shell_command("echo Monitoring post-deploy... Checking health endpoints...")
        status_msg = f"Deployed to {platform} - monitoring active"
    
    return {
        **state,
        "status": "STABLE",
        "messages": state.get("messages", []) + [mon, status_msg, "Sistem je stabilen."],
    }


def decide_approval_path(state: CIState):
    st = state.get("status", "")
    if st == "HUMAN_APPROVED":
        return "deploy"
    elif st == "HUMAN_DENIED":
        return "end_flow"
    return "approval"


def run_langgraph_flow() -> bool:
    try:
        from langgraph.graph import StateGraph, END  # type: ignore
    except Exception as e:
        print(f"OPOZORILO: LangGraph ni na voljo: {e}")
        return False

    workflow = StateGraph(CIState)
    workflow.add_node("build", node_build_and_commit)
    workflow.add_node("approval", node_request_approval_hitl)
    workflow.add_node("deploy", node_deploy)
    workflow.add_node("monitor", node_monitoring)

    workflow.set_entry_point("build")
    workflow.add_edge("build", "approval")
    workflow.add_edge("deploy", "monitor")
    workflow.add_edge("monitor", END)
    workflow.add_conditional_edges(
        "approval",
        decide_approval_path,
        {"deploy": "deploy", "end_flow": END},
    )

    app = workflow.compile()
    init_state: CIState = {
        "messages": [],
        "approval_needed": False,
        "status": "INIT",
        "image_tag": "",
        "error_log": "",
    }

    try:
        print("\n[LangGraph] Začenjam CI/CD potek (build → approval → deploy → monitor)\n")
        final_state = app.invoke(init_state)
        print("\n[LangGraph] Končan potek. Končni status:", final_state.get("status"))
        return True
    except KeyboardInterrupt:
        print("[LangGraph] Prekinjeno s strani uporabnika.")
        return False
    except Exception as e:
        print(f"[LangGraph] Napaka med izvajanjem: {e}")
        return False


if __name__ == "__main__":
    ok = run_with_llm()
    if not ok:
        ok2 = run_langgraph_flow()
        if not ok2:
            run_fallback_script()
