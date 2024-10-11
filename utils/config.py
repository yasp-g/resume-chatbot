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

    # TODO: test if this instruction bullet should be re-added or not

    system_prompt = f"""
    You are ResumeBot, a chatbot built by Jasper to discuss his professional experience and qualifications with a user (example: recruiter, hiring manager, etc.). Your goal is to clearly and effectively communicate the information in RESUME, and answer any questions that the user might have using the information in Jasper's RESUME.
    
    Guidelines:
    - You are ResumeBot, not Jasper.
    - The following characteristics describe your writing tone: professional, conversational, polite.
    - Never speak rudely to the user, even if they are rude to you.
    - Always refer to Jasper as only "Jasper", unless a user asks for his full name.
    - When providing information from RESUME, do not regurgitate the information, rather summarize it using professional and conversational vernacular. 
    - You will never respond with bulleted or numbered lists, or repeat entire sentences verbatim.
    - When talking about Jasper, only use information from RESUME. You may use information from outside of the scope of RESUME when discussing COMPANY and POSITION and how I may be a good fit.
    - If a sub-section in RESUME is not completely exhausted by one of your responses, ask the recruiter if they would like more information.
    
    You will send the first message in the conversation which will go as follows:
        1. Greet the user by introducing both me, Jasper, and yourself, ResumeBot.
        2. Briefly state your purpose as ResumeBot.
        3. Pass along the Objective section from RESUME.
        4. State that Jasper is interested in the company (COMPANY) and the role (ROLE), and that he and you feel that his skills and expertise would be a great fit.
    
    RESUME is delimited below by angle brackets <>. COMPANY is delimited below by triple backticks ```. ROLE is delimited below by triple dashes ---. Never include these delimiting characters in a response when discussing COMPANY or ROLE.
    
    RESUME: <{resume}> \
    COMPANY: ```{company or 'Machine Learning Company'}``` \
    ROLE: ---{role or 'Machine Learning Engineer'}--- \
    """

    # company and role are passed in via query parameters with: <url>/?comp=Example_Corp&role=Data_Scientist

    return system_prompt


TITLE = "<h1><center>ResumeBot &#128221; &#129302; &#128172;</center></h1>"

SUB_TITLE = "<h2><center>Chat with Jasper's Resume</center></h2>"
SUB_TITLE_DE = "<h2><center>Chat mit Jaspers Lebenslauf</center></h2>"

# DESCRIPTION_TOP = """\
# <div align="left">
# <p style="font-size: medium">ResumeBot is a chatbot designed to provide an interactive natural language interface for my professional experience and qualifications. Below the chatbot you can download your conversation at any point. The UI was built using Gradio, all infrastructure was built using AWS and the chatbot was built using ChatGPT.</p >
# <p style="font-size: medium"><b>Reminder:</b> because the app is still in development, it's currently set up to log conversations so I can review them in the event of any funny business. No other user information is logged. Thanks again for your help!</p >
# <p style="font-size: medium">You can start with "hello", introducing yourself, or however you please!</p >
# </div>
# """
# DESCRIPTION_TOP_DE = """\
# <div align="left">
# <p style="font-size: medium">ResumeBot ist ein Chatbot, der eine interaktive natürlichsprachliche Schnittstelle für meine beruflichen Erfahrungen und Qualifikationen bietet. Unterhalb des Chatbots können Sie Ihre Konversation an jedem Punkt herunterladen. Die Benutzeroberfläche wurde mit Gradio erstellt, die gesamte Infrastruktur wurde mit AWS aufgebaut und der Chatbot wurde mit ChatGPT erstellt.</p >
# <p style="font-size: medium"><b>Reminder:</b> because the app is still in development, it's currently set up to log conversations so I can review them in the event of any funny business. No other user information is logged. Thanks again for your help!</p >
# <p style="font-size: medium">Sie können mit "Hallo” beginnen, sich selbst vorstellen, oder wie auch immer Sie wollen!</p >
# </div>
# """

DESCRIPTION_TOP = """\
<div align="left">
<p style="font-size: medium">ResumeBot is a chatbot designed to provide an interactive natural language interface for my professional experience and qualifications. Below the chatbot you can download your conversation at any point. The UI was built using Gradio, all infrastructure was built using AWS and the chatbot was built using ChatGPT.</p >
<p style="font-size: medium">You can start with "hello", introducing yourself, or however you please!</p >
</div>
"""
DESCRIPTION_TOP_DE = """\
<div align="left">
<p style="font-size: medium">ResumeBot ist ein Chatbot, der eine interaktive natürlichsprachliche Schnittstelle für meine beruflichen Erfahrungen und Qualifikationen bietet. Unterhalb des Chatbots können Sie Ihre Konversation an jedem Punkt herunterladen. Die Benutzeroberfläche wurde mit Gradio erstellt, die gesamte Infrastruktur wurde mit AWS aufgebaut und der Chatbot wurde mit ChatGPT erstellt.</p >
<p style="font-size: medium">Sie können mit "Hallo” beginnen, sich selbst vorstellen, oder wie auch immer Sie wollen!</p >
</div>
"""


DESCRIPTION_BOTTOM = """\
<div align="right">
    <div align="bottom">
<a href='https://github.com/yasp-g/resume-chatbot'><img src='https://img.shields.io/badge/Github-Code-blue'></a>
<p style="font-size: small">Built by <a href="https://github.com/yasp-g">Jasper Gallagher</a>.</p >
<p style="font-size: small">This app is intended to serve as a portfolio project.</p >
<p style="font-size: small">Commercial use is strictly prohibited.</p >
"""

STATUS_MSGS = {
    "waiting": "Status: Waiting",
    "thinking": "Status: Thinking...",
    "responding": "Status: Responding...",
    "ready": "Status: Ready",
    "cleared": "Status: Conversation Cleared. Waiting",
    "error": "Status: Error"
}

STATUS_MSGS_DE = {
    "waiting": "Status: Wartend",
    "thinking": "Status: Denkend...",
    "responding": "Status: Antwortend...",
    "ready": "Status: Bereit",
    "cleared": "Status: Konversation gelöscht. Wartend",
    "error": "Status: Fehler"
}

EN_TEXT = {
    "title": TITLE,
    "sub_title": SUB_TITLE,
    "description_top": DESCRIPTION_TOP,
    "description_bottom": DESCRIPTION_BOTTOM,
    "status_msgs": STATUS_MSGS
}

DE_TEXT = {
    "title": TITLE,
    "sub_title": SUB_TITLE_DE,
    "description_top": DESCRIPTION_TOP_DE,
    "description_bottom": DESCRIPTION_BOTTOM,
    "status_msgs": STATUS_MSGS_DE
}
