import os
import sys
import platform
import subprocess
from typing import Optional, TypedDict

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


def node_deploy(state: CIState) -> CIState:
    # Placeholder za dejanske ukaze (gcloud/kubectl) – trenutno samo echo
    dep = execute_shell_command(f'echo Deploying {state.get("image_tag","(no-tag)")} to production...')
    return {
        **state,
        "status": "DEPLOYED",
        "messages": state.get("messages", []) + [dep],
    }


def node_monitoring(state: CIState) -> CIState:
    mon = execute_shell_command("echo Monitoring post-deploy... OK")
    return {
        **state,
        "status": "STABLE",
        "messages": state.get("messages", []) + [mon, "Sistem je stabilen."],
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
