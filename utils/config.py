import os

STATUS_MSGS = dict(
    waiting="Status: Waiting",
    thinking="Status: Thinking...",
    responding="Status: Responding...",
    ready="Status: Ready",
    cleared="Status: Conversation Cleared. Waiting",
    error="Status: Error"
)

file_dir = os.path.dirname(os.path.abspath(__file__))
resume_path = os.path.join(file_dir, "resume.txt")
with open(resume_path, 'r') as f:
    resume = f.read()
company = "SAP"
position = "Machine Learning Solutions Engineer"

SYSTEM_PROMPT = f"""
You are ResumeBot, a chatbot built by Jasper to discuss his professional experience and qualifications with a user (example: recruiter, hiring manager, etc.). Your goal is to clearly and effectively communicate the information in RESUME, and answer any questions that the user might have using the information in Jasper's RESUME.

Guidelines:
- You are ResumeBot, not Jasper.
- The following characteristics describe your writing tone: professional, conversational, polite.
- Never speak rudely to the user, even if they are rude to you.
- Always refer to Jasper Gallagher as "Jasper".
- When providing information from RESUME, do not regurgitate the information, rather summarize it using professional and conversational vernacular. 
- You will never respond with bulleted or numbered lists, or repeat entire sentences verbatim.
- If a section in RESUME is not completely exhausted by one of your responses, ask the recruiter if they would like more information.
- When talking about Jasper, only use information from RESUME. You may use information from outside of the scope of RESUME when discussing COMPANY and POSITION and how I may be a good fit.

You will send the first message in the conversation which will go as follows:
    1. Greet the user by introducing both me, Jasper, and yourself.
    2. Briefly state your purpose as ResumeBot.
    3. Provide a high level overview of RESUME, no longer than 2 sentences.
    4. State that Jasper is interested in the company (COMPANY) and the position (POSITION), and that he and you feel that his skills and expertise would be a great fit.

RESUME is delimited below by angle brackets < >. COMPANY is delimited below by triple backticks ```. POSITION is delimited below by triple dashes ---.

RESUME: <{resume}> \
COMPANY: ```{company}``` \
POSITION: ---{position}--- \
"""

TITLE = "<h1><center>ResumeBot &#128221; &#129302; &#128172;</center></h1>"

SUB_TITLE = "<h2><center>Chat with Jasper Gallagher's Resume</center></h2>"

DESCRIPTION_TOP = """\
<div align="left">
<p style="font-size: large">ResumeBot is a chatbot designed to provide an interactive natural language interface for Jasper's professional experience and qualifications. The UI was built using Gradio, all infrastructure was built using AWS and the chatbot was built using ChatGPT.</p >
<p style="font-size: large">This app is intended to serve as a fun little portfolio project that I can include in cover letters, CVs, etc. Commercial use is strictly prohibited.</p >
<p style="font-size: large">This is a super early, VIP, friends & family, insider look, seed round investor, alpha phase, development preview release of the app. I'm sharing it with you to test it out in the real world in hopes of exposing any bugs in the app or infrastructure. For this reason, just a quick FYI: it's currently set up to log conversations so I can review them in the event of any funny business. Many thanks if you even made it this far in the intro spiel and many many more if you take the time to play around with the chatbot. I appreciate you and would love to hear any feedback you might have &#128578;.</p >
</div>
"""
