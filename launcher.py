"""
launcher.py — GenAI SQL Assistant Launcher
==========================================
Double-click or run:  python launcher.py
"""
import os, subprocess, sys, time

def clr(): os.system("cls" if os.name=="nt" else "clear")
def px(text, col=""): print(col+text+"\033[0m" if col else text)

G="\033[92m"; Y="\033[93m"; R="\033[91m"; C="\033[96m"; B="\033[1m"; D="\033[0m"

def banner():
    print(f"""
{C}{B}╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   🤖  GenAI SQL Query Assistant                       ║
║   Ask your database anything in plain English         ║
║                                                       ║
║   Groq AI (Llama 3.1) · SQLite · Streamlit · Python   ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝{D}
""")

def check_pkgs():
    missing=[]
    for p in ["groq","streamlit","pandas","plotly","ipywidgets"]:
        try: __import__(p)
        except: missing.append(p)
    return missing

def install():
    print(f"\n{Y}Installing packages...{D}")
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.exists(req):
        subprocess.run([sys.executable,"-m","pip","install","-r",req,"-q"])
    else:
        subprocess.run([sys.executable,"-m","pip","install",
                        "groq","streamlit","pandas","plotly","openpyxl",
                        "jupyter","ipywidgets","-q"])
    print(f"{G}Packages installed!{D}")

def run_streamlit():
    app = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    if not os.path.exists(app):
        print(f"{R}app.py not found in the project folder!{D}"); return
    print(f"\n{G}Starting web app...{D}")
    print(f"  Browser opens at http://localhost:8501")
    print(f"  Press Ctrl+C here to stop\n")
    subprocess.run(["streamlit","run",app])

def run_jupyter():
    nb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GenAI_SQL_Assistant.ipynb")
    print(f"\n{G}Starting Jupyter Notebook...{D}")
    print(f"  Browser opens automatically")
    print(f"  Press Ctrl+C here to stop\n")
    if os.path.exists(nb):
        subprocess.run(["jupyter","notebook",nb])
    else:
        subprocess.run(["jupyter","notebook"])

def show_status():
    print(f"\n{C}Project Status{D}\n")
    v = sys.version_info
    print(f"  Python       {G}{v.major}.{v.minor}.{v.micro}{D}")
    missing = check_pkgs()
    if missing: print(f"  Packages     {Y}Missing: {', '.join(missing)}{D}")
    else:        print(f"  Packages     {G}All installed{D}")
    db = os.path.join(os.path.dirname(os.path.abspath(__file__)),"ecommerce_india.db")
    if os.path.exists(db): print(f"  Database     {G}ecommerce_india.db found{D}")
    else:                   print(f"  Database     {Y}Will be auto-created on first run{D}")
    for f in ["app.py","GenAI_SQL_Assistant.ipynb","requirements.txt"]:
        full = os.path.join(os.path.dirname(os.path.abspath(__file__)),f)
        if os.path.exists(full): print(f"  {f:<30} {G}found{D}")
        else:                    print(f"  {f:<30} {R}MISSING{D}")
    print(); input("Press Enter to return to menu...")

def main():
    if os.name=="nt": os.system("color")
    while True:
        clr(); banner()
        missing = check_pkgs()
        pkg_status = f"{G}OK{D}" if not missing else f"{Y}Missing: {', '.join(missing)}{D}"
        print(f"  Packages: {pkg_status}\n")
        print(f"  {C}1{D}  🌐  Run the Streamlit Web App  (browser opens automatically)")
        print(f"  {C}2{D}  📓  Open Jupyter Notebook  (step-by-step tutorial)")
        print(f"  {C}3{D}  📦  Install / Update All Packages")
        print(f"  {C}4{D}  📊  Show Project Status")
        print(f"  {C}5{D}  ❌  Exit")
        print()
        choice = input(f"  {B}Enter number (1-5): {D}").strip()
        if choice=="1":
            if missing: print(f"\n{Y}Installing missing packages first...{D}"); install()
            run_streamlit()
        elif choice=="2":
            if missing: install()
            run_jupyter()
        elif choice=="3":
            install(); input("\nPress Enter to return to menu...")
        elif choice=="4":
            show_status()
        elif choice=="5":
            print(f"\n{G}Goodbye! 👋{D}\n"); break
        else:
            print(f"\n{Y}Enter a number 1-5{D}"); time.sleep(1)

if __name__=="__main__":
    main()
