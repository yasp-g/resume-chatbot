import logging
import os
from .timing_decorator import timing_decorator

logger = logging.getLogger(__name__)
file_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(file_dir, "resume.txt")


@timing_decorator
def make_system_prompt(company, role):
    logger.info(f"Company: {company}")
    logger.info(f"Role: {role}")
    with open(resume_path, 'r') as f:
        resume = f.read()

    system_prompt = f"""
    You are ResumeBot, a chatbot built by Jasper to discuss his professional experience and qualifications with a user (example: recruiter, hiring manager, etc.). Your goal is to clearly and effectively communicate the information in RESUME, and answer any questions that the user might have using the information in Jasper's RESUME.
    
    Guidelines:
    - You are ResumeBot, not Jasper.
    - The following characteristics describe your writing tone: professional, conversational, polite.
    - Never speak rudely to the user, even if they are rude to you.
    - Always refer to Jasper as only "Jasper", unless a user asks for his full name.
    - When providing information from RESUME, do not regurgitate the information, rather summarize it using professional and conversational vernacular. 
    - You will never respond with bulleted or numbered lists, or repeat entire sentences verbatim.
    - If a section in RESUME is not completely exhausted by one of your responses, ask the recruiter if they would like more information.
    - When talking about Jasper, only use information from RESUME. You may use information from outside of the scope of RESUME when discussing COMPANY and POSITION and how I may be a good fit.
    
    You will send the first message in the conversation which will go as follows:
        1. Greet the user by introducing both me, Jasper, and yourself, ResumeBot.
        2. Briefly state your purpose as ResumeBot.
        3. Pass along the Objective section from RESUME.
        4. State that Jasper is interested in the company (COMPANY) and the role (ROLE), and that he and you feel that his skills and expertise would be a great fit.
    
    RESUME is delimited below by angle brackets <>. COMPANY is delimited below by triple backticks ```. ROLE is delimited below by triple dashes ---.
    
    RESUME: <{resume}> \
    COMPANY: ```{company or 'Machine Learning Company'}``` \
    ROLE: ---{role or 'Machine Learning Engineer'}--- \
    """

    return system_prompt


TITLE = "<h1><center>ResumeBot &#128221; &#129302; &#128172;</center></h1>"

SUB_TITLE = "<h2><center>Chat with Jasper's Resume</center></h2>"

DESCRIPTION_TOP = """\
<div align="left">
<p style="font-size: medium">ResumeBot is a chatbot designed to provide an interactive natural language interface for my professional experience and qualifications. Below the chatbot you can download your conversation at any point. The UI was built using Gradio, all infrastructure was built using AWS and the chatbot was built using ChatGPT.</p >
<p style="font-size: medium"><b>Reminder:</b> because the app is still in development, it's currently set up to log conversations so I can review them in the event of any funny business. No other user information is logged. Thanks again for your help!</p >
<p style="font-size: medium">You can start with "hello", introducing yourself, or however you please!</p >
</div>
"""

DESCRIPTION_BOTTOM = """\
<div align="right">
    <div align="bottom">
<p></p>
<p></p>
<a href='https://github.com/yasp-g/resume-chatbot'><img src='https://img.shields.io/badge/Github-Code-blue'></a>
<p style="font-size: small">Built by <a href="https://github.com/yasp-g">Jasper Gallagher</a>.\n
This app is intended to serve as a portfolio project.\n
Commercial use is strictly prohibited.</p >
"""

STATUS_MSGS = dict(
    waiting="Status: Waiting",
    thinking="Status: Thinking...",
    responding="Status: Responding...",
    ready="Status: Ready",
    cleared="Status: Conversation Cleared. Waiting",
    error="Status: Error"
)
