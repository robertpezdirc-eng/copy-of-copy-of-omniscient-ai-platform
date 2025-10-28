import os
import sys
import platform
import subprocess
from typing import Optional

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
    steps = [
        "ls -a",
        "cat Dockerfile",
        "cat README.md",
        "docker build -t my-llm-app-prod:latest .",
        "git add .",
        "git commit -m \"Auto CI/CD Build by Agent\"",
    ]
    for s in steps:
        print(f"\n>>> Izvajam: {s}")
        print(execute_shell_command(s))


if __name__ == "__main__":
    ok = run_with_llm()
    if not ok:
        run_fallback_script()